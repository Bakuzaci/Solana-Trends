"""
Social listening service for discovering meta relationships.

Monitors web sources to understand how metas relate to each other,
like how "clawd" spawned "molt" coins.
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import httpx


@dataclass
class MetaDiscovery:
    """A discovered meta relationship."""
    source_keyword: str
    related_keyword: str
    relationship_type: str  # derivative, variant, sequel, parody
    confidence: float
    context: str  # where/how it was discovered


@dataclass
class TrendingTopic:
    """A trending topic in the Solana meme coin space."""
    keyword: str
    mention_count: int
    co_keywords: List[str]
    source: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)


# Known meta relationships (seed data)
KNOWN_RELATIONSHIPS = [
    # AI Agent ecosystem relationships
    MetaDiscovery("clawd", "molt", "derivative", 0.95, "clawd meta spawned molt coins after rename"),
    MetaDiscovery("clawd", "openclaw", "sequel", 0.95, "clawd renamed to openclaw"),
    MetaDiscovery("molt", "openclaw", "sequel", 0.95, "moltbot renamed to openclaw"),
    MetaDiscovery("ai16z", "eliza", "framework", 0.95, "ai16z uses ElizaOS framework"),
    MetaDiscovery("ai16z", "degenai", "derivative", 0.9, "degenai built on ai16z/eliza stack"),
    MetaDiscovery("goat", "ai", "category", 0.95, "goatseus maximus AI agent token"),
    MetaDiscovery("zerebro", "ai", "category", 0.9, "zerebro autonomous AI agent"),
    MetaDiscovery("griffain", "ai", "category", 0.9, "griffain AI agent platform"),
    MetaDiscovery("arc", "ai", "category", 0.9, "arc AI agent infrastructure"),
    MetaDiscovery("openclaw", "ai", "category", 0.9, "openclaw AI assistant"),

    # Traditional meme relationships
    MetaDiscovery("pepe", "frog", "variant", 0.9, "pepe led to many frog-themed coins"),
    MetaDiscovery("doge", "dog", "category", 0.95, "dogecoin category"),
    MetaDiscovery("shiba", "dog", "variant", 0.9, "shiba inu dog variant"),
    MetaDiscovery("bonk", "dog", "variant", 0.85, "bonk dog meme"),
    MetaDiscovery("wif", "dog", "variant", 0.9, "dogwifhat"),
    MetaDiscovery("mew", "cat", "variant", 0.9, "cat in dogs world"),
    MetaDiscovery("popcat", "cat", "variant", 0.85, "popcat meme"),
    MetaDiscovery("trump", "politics", "category", 0.95, "political tokens"),
    MetaDiscovery("fartcoin", "meme", "category", 0.8, "absurdist meme"),
    MetaDiscovery("bome", "book", "category", 0.85, "book of meme"),
    MetaDiscovery("pnut", "animal", "category", 0.8, "peanut the squirrel"),
    MetaDiscovery("moodeng", "animal", "category", 0.8, "moo deng hippo"),
]


# Keywords to search for related metas
META_SEARCH_PATTERNS = {
    # AI Agent ecosystem
    "clawd": ["molt", "claw", "openclaw", "shed", "exoskeleton", "crab", "lobster"],
    "openclaw": ["clawd", "molt", "moltbot", "claw", "ai", "agent"],
    "ai16z": ["eliza", "elizaos", "degenai", "agent", "dao", "vc"],
    "goat": ["goatseus", "maximus", "truth", "terminal", "ai"],
    "zerebro": ["hyperstition", "autonomous", "ai", "agent"],
    "griffain": ["ai", "agent", "soulbound", "nft"],
    "arc": ["rig", "ai", "agent", "rust"],

    # Traditional meme patterns
    "pepe": ["frog", "kek", "rare", "feels", "smug"],
    "doge": ["dog", "shiba", "woof", "bone", "treat", "wif", "bonk"],
    "cat": ["mew", "meow", "kitty", "whiskers", "purr", "popcat"],
    "trump": ["maga", "politics", "president", "freedom", "america"],
    "ai": ["agent", "gpt", "neural", "bot", "artificial", "eliza", "autonomous"],
    "moon": ["rocket", "lambo", "pump", "ath", "launch"],
}


def extract_keywords_from_text(text: str) -> List[str]:
    """Extract potential meta keywords from text."""
    # Common meme coin keywords
    patterns = [
        r'\b([A-Z]{2,10})\b',  # Uppercase ticker symbols
        r'\$([A-Za-z]{2,10})\b',  # Cashtag format
        r'#([A-Za-z]{2,20})\b',  # Hashtags
    ]

    keywords = []
    text_lower = text.lower()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        keywords.extend([m.lower() for m in matches])

    # Also look for known meta patterns
    for meta, related in META_SEARCH_PATTERNS.items():
        if meta in text_lower:
            keywords.append(meta)
        for r in related:
            if r in text_lower:
                keywords.append(r)

    return list(set(keywords))


def find_co_occurring_keywords(text: str, target_keyword: str) -> List[str]:
    """Find keywords that co-occur with a target keyword in text."""
    text_lower = text.lower()
    if target_keyword.lower() not in text_lower:
        return []

    # Extract all keywords from the text
    all_keywords = extract_keywords_from_text(text)

    # Remove the target keyword and return co-occurring ones
    return [k for k in all_keywords if k.lower() != target_keyword.lower()]


async def _fetch_trending_from_dexscreener() -> List[TrendingTopic]:
    """Fetch trending tokens from DexScreener to understand current metas."""
    topics = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.dexscreener.com/latest/dex/search?q=solana",
                timeout=15.0,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])[:50]

                # Count keyword occurrences
                keyword_counts: Dict[str, int] = defaultdict(int)
                keyword_co_occurrences: Dict[str, Set[str]] = defaultdict(set)

                for pair in pairs:
                    base = pair.get("baseToken", {})
                    name = (base.get("name", "") or "").lower()
                    symbol = (base.get("symbol", "") or "").lower()

                    # Extract keywords from name and symbol
                    text = f"{name} {symbol}"
                    keywords = extract_keywords_from_text(text)

                    for kw in keywords:
                        keyword_counts[kw] += 1
                        for other_kw in keywords:
                            if other_kw != kw:
                                keyword_co_occurrences[kw].add(other_kw)

                # Create trending topics for high-count keywords
                for kw, count in sorted(keyword_counts.items(), key=lambda x: -x[1])[:20]:
                    if count >= 2:  # At least 2 mentions
                        topics.append(TrendingTopic(
                            keyword=kw,
                            mention_count=count,
                            co_keywords=list(keyword_co_occurrences.get(kw, set()))[:10],
                            source="dexscreener"
                        ))

    except Exception as e:
        print(f"Error fetching trending from DexScreener: {e}")

    return topics


def analyze_meta_relationships(
    topics: List[TrendingTopic],
    existing_keywords: Set[str]
) -> List[MetaDiscovery]:
    """
    Analyze trending topics to discover meta relationships.

    Looks for patterns like:
    - New keywords appearing with known metas
    - Keywords that frequently co-occur
    - Derivative naming patterns (e.g., clawd -> molt)
    """
    discoveries = []

    # Look for known patterns
    for topic in topics:
        keyword = topic.keyword.lower()

        # Check against known meta patterns
        for meta, related_keywords in META_SEARCH_PATTERNS.items():
            if keyword in related_keywords and meta not in discoveries:
                discoveries.append(MetaDiscovery(
                    source_keyword=meta,
                    related_keyword=keyword,
                    relationship_type="variant",
                    confidence=0.7,
                    context=f"Found {keyword} as related to {meta} pattern"
                ))

        # Check co-occurring keywords for relationships
        for co_kw in topic.co_keywords:
            co_kw_lower = co_kw.lower()

            # If both are trending, they might be related
            if co_kw_lower in existing_keywords:
                # Determine relationship type based on naming
                if _is_derivative_name(keyword, co_kw_lower):
                    rel_type = "derivative"
                    conf = 0.75
                elif _is_variant_name(keyword, co_kw_lower):
                    rel_type = "variant"
                    conf = 0.6
                else:
                    rel_type = "associated"
                    conf = 0.5

                discoveries.append(MetaDiscovery(
                    source_keyword=co_kw_lower,
                    related_keyword=keyword,
                    relationship_type=rel_type,
                    confidence=conf,
                    context=f"Co-occurring keywords in {topic.source}"
                ))

    return discoveries


def _is_derivative_name(name1: str, name2: str) -> bool:
    """Check if one name is a derivative of another."""
    # Check for prefix/suffix relationships
    if name1.startswith(name2) or name2.startswith(name1):
        return True
    if name1.endswith(name2) or name2.endswith(name1):
        return True
    return False


def _is_variant_name(name1: str, name2: str) -> bool:
    """Check if names are variants (similar but different)."""
    # Check for similar lengths and some shared characters
    if abs(len(name1) - len(name2)) <= 3:
        shared = set(name1) & set(name2)
        if len(shared) >= min(len(name1), len(name2)) * 0.5:
            return True
    return False


async def discover_meta_relationships() -> Tuple[List[TrendingTopic], List[MetaDiscovery]]:
    """
    Main function to discover meta relationships through social listening.

    Returns:
        Tuple of (trending topics, discovered relationships)
    """
    print("Starting social listening for meta relationships...")

    # Fetch trending data
    dex_topics = await _fetch_trending_from_dexscreener()

    all_topics = dex_topics
    print(f"Found {len(all_topics)} trending topics")

    # Get existing keywords
    existing_keywords = set(t.keyword.lower() for t in all_topics)

    # Analyze for relationships
    discoveries = analyze_meta_relationships(all_topics, existing_keywords)

    # Add known relationships that aren't already discovered
    existing_keys = set((d.source_keyword, d.related_keyword) for d in discoveries)
    for known in KNOWN_RELATIONSHIPS:
        key = (known.source_keyword, known.related_keyword)
        if key not in existing_keys:
            discoveries.append(known)

    print(f"Discovered {len(discoveries)} meta relationships")

    return all_topics, discoveries


def search_related_metas(
    query: str,
    all_relationships: List[MetaDiscovery]
) -> List[MetaDiscovery]:
    """
    Search for metas related to a query.

    Args:
        query: Search term (e.g., "claw", "molt", "dog")
        all_relationships: List of all known meta relationships

    Returns:
        List of related meta discoveries
    """
    query_lower = query.lower()
    results = []

    for rel in all_relationships:
        # Direct match on source or related keyword
        if query_lower in rel.source_keyword.lower() or query_lower in rel.related_keyword.lower():
            results.append(rel)
            continue

        # Partial match
        if (rel.source_keyword.lower() in query_lower or
            rel.related_keyword.lower() in query_lower):
            results.append(rel)

    # Sort by confidence
    results.sort(key=lambda x: x.confidence, reverse=True)

    return results


def get_all_known_relationships() -> List[MetaDiscovery]:
    """Get all known meta relationships."""
    return KNOWN_RELATIONSHIPS.copy()
