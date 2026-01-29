"""
Breakout meta detection service using clustering.

Detects emerging trends and breakout metas by clustering
tokens based on name/symbol similarity using DBSCAN.
"""
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from collections import Counter

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class BreakoutCluster:
    """Represents a detected breakout meta cluster."""
    cluster_id: int
    cluster_name: str
    tokens: List[str]  # List of token addresses
    token_names: List[str]  # List of token names
    size: int
    common_keywords: List[str]
    confidence_score: float  # 0-1


@dataclass
class TokenInfo:
    """Minimal token info for clustering."""
    address: str
    name: str
    symbol: str


class BreakoutDetector:
    """
    Detects breakout metas using DBSCAN clustering on token names.

    Uses TF-IDF vectorization with character n-grams to capture
    name similarities, then clusters using DBSCAN.
    """

    def __init__(
        self,
        min_cluster_size: int = 5,
        eps: float = 0.5,
        min_samples: int = 3,
    ):
        """
        Initialize the breakout detector.

        Args:
            min_cluster_size: Minimum tokens to form a valid cluster
            eps: DBSCAN epsilon parameter (max distance between samples)
            min_samples: DBSCAN min_samples parameter
        """
        self.min_cluster_size = min_cluster_size
        self.eps = eps
        self.min_samples = min_samples

        # TF-IDF vectorizer with character n-grams
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=1000,
            lowercase=True,
        )

    def detect_breakout_metas(
        self,
        tokens: List[TokenInfo],
        existing_categories: Optional[Dict[str, List[str]]] = None
    ) -> List[BreakoutCluster]:
        """
        Detect breakout metas from a list of tokens.

        Args:
            tokens: List of TokenInfo objects to analyze
            existing_categories: Optional dict of existing category keywords
                                to filter out known trends

        Returns:
            List of BreakoutCluster objects representing detected metas
        """
        if len(tokens) < self.min_cluster_size:
            return []

        # Prepare text data for vectorization
        texts = [f"{t.name} {t.symbol}".lower() for t in tokens]

        # Vectorize using TF-IDF
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
        except ValueError:
            # Not enough data to vectorize
            return []

        # Convert to dense array for DBSCAN
        # Use cosine distance (1 - cosine similarity)
        from sklearn.metrics.pairwise import cosine_distances
        distance_matrix = cosine_distances(tfidf_matrix)

        # Run DBSCAN clustering
        clustering = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric="precomputed",
        )
        labels = clustering.fit_predict(distance_matrix)

        # Process clusters
        clusters = []
        unique_labels = set(labels)

        for label in unique_labels:
            if label == -1:  # Noise points
                continue

            # Get tokens in this cluster
            cluster_mask = labels == label
            cluster_indices = np.where(cluster_mask)[0]

            if len(cluster_indices) < self.min_cluster_size:
                continue

            cluster_tokens = [tokens[i] for i in cluster_indices]
            cluster_texts = [texts[i] for i in cluster_indices]

            # Extract common keywords
            common_keywords = self._extract_common_keywords(cluster_texts)

            # Filter out if matches existing category
            if existing_categories:
                is_known = self._matches_known_category(
                    common_keywords,
                    existing_categories
                )
                if is_known:
                    continue

            # Generate cluster name
            cluster_name = self._generate_cluster_name(common_keywords)

            # Calculate confidence score
            confidence = self._calculate_confidence(
                cluster_tokens,
                tfidf_matrix[cluster_indices]
            )

            cluster = BreakoutCluster(
                cluster_id=label,
                cluster_name=cluster_name,
                tokens=[t.address for t in cluster_tokens],
                token_names=[t.name for t in cluster_tokens],
                size=len(cluster_tokens),
                common_keywords=common_keywords[:5],  # Top 5 keywords
                confidence_score=confidence,
            )
            clusters.append(cluster)

        # Sort by size and confidence
        clusters.sort(key=lambda c: (c.size, c.confidence_score), reverse=True)

        return clusters

    def _extract_common_keywords(
        self,
        texts: List[str],
        min_frequency: float = 0.3
    ) -> List[str]:
        """
        Extract common keywords from cluster texts.

        Args:
            texts: List of text strings
            min_frequency: Minimum frequency (0-1) for a word to be considered

        Returns:
            List of common keywords sorted by frequency
        """
        # Tokenize texts into words
        all_words = []
        for text in texts:
            words = text.split()
            all_words.extend(words)

        # Count word frequencies
        word_counts = Counter(all_words)
        total_texts = len(texts)

        # Filter by minimum frequency
        common_words = [
            word for word, count in word_counts.most_common()
            if count / total_texts >= min_frequency
            and len(word) >= 3  # Minimum word length
        ]

        return common_words

    def _matches_known_category(
        self,
        keywords: List[str],
        categories: Dict[str, List[str]]
    ) -> bool:
        """
        Check if keywords match a known category.

        Args:
            keywords: List of cluster keywords
            categories: Dictionary of category keywords

        Returns:
            True if matches known category
        """
        keyword_set = set(k.lower() for k in keywords)

        for cat_keywords in categories.values():
            cat_keyword_set = set(k.lower() for k in cat_keywords)
            overlap = keyword_set & cat_keyword_set

            # If more than 50% overlap, consider it known
            if len(overlap) > len(keyword_set) * 0.5:
                return True

        return False

    def _generate_cluster_name(self, keywords: List[str]) -> str:
        """
        Generate a name for the cluster based on keywords.

        Args:
            keywords: List of common keywords

        Returns:
            Generated cluster name
        """
        if not keywords:
            return "Unknown Meta"

        # Use the most common keyword(s)
        if len(keywords) >= 2:
            return f"{keywords[0].title()}-{keywords[1].title()} Meta"
        return f"{keywords[0].title()} Meta"

    def _calculate_confidence(
        self,
        tokens: List[TokenInfo],
        tfidf_subset: np.ndarray
    ) -> float:
        """
        Calculate confidence score for a cluster.

        Based on:
        - Cluster cohesion (average similarity)
        - Cluster size
        - Temporal proximity (if tokens have timestamps)

        Args:
            tokens: List of tokens in the cluster
            tfidf_subset: TF-IDF vectors for cluster tokens

        Returns:
            Confidence score between 0 and 1
        """
        if len(tokens) < 2:
            return 0.0

        # Calculate average pairwise similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(tfidf_subset)

        # Get upper triangle (excluding diagonal)
        n = len(tokens)
        upper_tri = similarities[np.triu_indices(n, k=1)]

        avg_similarity = np.mean(upper_tri) if len(upper_tri) > 0 else 0

        # Size factor (more tokens = more confident)
        size_factor = min(1.0, len(tokens) / 20)

        # Combined confidence
        confidence = (avg_similarity * 0.7) + (size_factor * 0.3)

        return round(confidence, 3)


def detect_breakout_metas(
    tokens: List[TokenInfo],
    min_cluster_size: int = 5,
    eps: float = 0.5,
) -> List[BreakoutCluster]:
    """
    Convenience function to detect breakout metas.

    Args:
        tokens: List of TokenInfo objects
        min_cluster_size: Minimum cluster size
        eps: DBSCAN epsilon parameter

    Returns:
        List of detected BreakoutCluster objects
    """
    detector = BreakoutDetector(
        min_cluster_size=min_cluster_size,
        eps=eps,
    )
    return detector.detect_breakout_metas(tokens)


def format_cluster_report(clusters: List[BreakoutCluster]) -> str:
    """
    Format clusters into a human-readable report.

    Args:
        clusters: List of BreakoutCluster objects

    Returns:
        Formatted report string
    """
    if not clusters:
        return "No breakout metas detected."

    lines = ["=" * 50, "BREAKOUT META DETECTION REPORT", "=" * 50, ""]

    for i, cluster in enumerate(clusters, 1):
        lines.append(f"#{i} {cluster.cluster_name}")
        lines.append(f"   Size: {cluster.size} tokens")
        lines.append(f"   Confidence: {cluster.confidence_score:.1%}")
        lines.append(f"   Keywords: {', '.join(cluster.common_keywords)}")
        lines.append(f"   Sample tokens: {', '.join(cluster.token_names[:5])}")
        lines.append("")

    return "\n".join(lines)
