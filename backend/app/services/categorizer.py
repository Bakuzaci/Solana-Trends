"""
Token categorization service.

Uses CoinGecko's pre-defined categories as primary source, with
keyword fallback for uncategorized tokens.
"""
from typing import Dict, List, Optional, Tuple


# =============================================================================
# CoinGecko Category Mapping
# =============================================================================

# Map CoinGecko categories to our display categories
COINGECKO_CATEGORY_MAP = {
    "pump-fun": ("PumpFun", "Ecosystem"),
    "solana-meme-coins": ("Solana Memes", "General"),
    "ai-meme-coins": ("AI Agents", "Meme"),
    "dog-themed-coins": ("Animals", "Dogs"),
    "cat-themed-coins": ("Animals", "Cats"),
    "frog-themed-coins": ("Animals", "Frogs"),
    "political-meme-coins": ("Politics", "General"),
    "trump-meme": ("Politics", "Trump"),
}

# =============================================================================
# Category Emoji Mapping
# =============================================================================

CATEGORY_EMOJIS: Dict[str, Dict[str, str]] = {
    "AI Agents": {
        "_default": "🤖",
        "Meme": "🤖",
        "Autonomous": "🦾",
    },
    "PumpFun": {
        "_default": "🎰",
        "Ecosystem": "🎰",
        "New": "🆕",
    },
    "Solana Memes": {
        "_default": "☀️",
        "General": "☀️",
        "Blue Chip": "💎",
    },
    "Animals": {
        "_default": "🐾",
        "Dogs": "🐕",
        "Cats": "🐱",
        "Frogs": "🐸",
        "Penguins": "🐧",
        "Other": "🦁",
    },
    "Politics": {
        "_default": "🏛️",
        "Trump": "🇺🇸",
        "General": "🗳️",
    },
    "Culture": {
        "_default": "🎭",
        "Internet": "💀",
        "Celebrities": "⭐",
    },
    "Uncategorized": {
        "_default": "✨",
    },
}


def get_category_emoji(primary_category: str, sub_category: Optional[str] = None) -> str:
    """Get the emoji for a category."""
    if primary_category not in CATEGORY_EMOJIS:
        return "📊"
    
    category_emojis = CATEGORY_EMOJIS[primary_category]
    
    if sub_category and sub_category in category_emojis:
        return category_emojis[sub_category]
    
    return category_emojis.get("_default", "📊")


# =============================================================================
# Keyword-based fallback categorization
# =============================================================================

# Simpler keyword sets for fallback categorization
KEYWORD_CATEGORIES = {
    ("AI Agents", "Meme"): [
        "ai", "gpt", "bot", "agent", "llm", "neural", "claude", "openai",
        "autonomous", "goat", "zerebro", "griffain", "arc", "eliza", "truth",
    ],
    ("Animals", "Dogs"): [
        "dog", "doge", "shiba", "inu", "wif", "bonk", "puppy", "pup",
    ],
    ("Animals", "Cats"): [
        "cat", "kitty", "kitten", "mew", "meow", "popcat",
    ],
    ("Animals", "Frogs"): [
        "frog", "pepe", "toad", "ribbit",
    ],
    ("Animals", "Penguins"): [
        "penguin", "pengu", "pudgy",
    ],
    ("Politics", "Trump"): [
        "trump", "maga", "donald",
    ],
    ("Culture", "Internet"): [
        "meme", "wojak", "chad", "based", "cope", "seethe",
    ],
}

# Build reverse index
KEYWORD_INDEX = {}
for (primary, sub), keywords in KEYWORD_CATEGORIES.items():
    for kw in keywords:
        KEYWORD_INDEX[kw.lower()] = (primary, sub)


def categorize_token(
    name: str,
    symbol: str,
    coingecko_category: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Categorize a token.
    
    Priority:
    1. CoinGecko category (if provided)
    2. Keyword matching on name/symbol
    
    Returns:
        Tuple of (primary_category, sub_category, detected_keywords)
    """
    # Use CoinGecko category if available
    if coingecko_category and coingecko_category in COINGECKO_CATEGORY_MAP:
        primary, sub = COINGECKO_CATEGORY_MAP[coingecko_category]
        return primary, sub, [coingecko_category]
    
    # Fall back to keyword matching
    import re
    combined = f"{name} {symbol}".lower()
    words = set(re.findall(r'[a-z0-9]+', combined))
    
    detected = []
    best_match = None
    
    for word in words:
        if word in KEYWORD_INDEX:
            primary, sub = KEYWORD_INDEX[word]
            detected.append(word)
            if best_match is None:
                best_match = (primary, sub)
    
    # Also check substrings for compound names like "dogwifhat"
    for keyword, (primary, sub) in KEYWORD_INDEX.items():
        if len(keyword) >= 3 and keyword in combined and keyword not in detected:
            detected.append(keyword)
            if best_match is None:
                best_match = (primary, sub)
    
    if best_match:
        return best_match[0], best_match[1], detected
    
    return None, None, []


# =============================================================================
# Category utilities
# =============================================================================

# Flat list of all categories for the old code
TREND_CATEGORIES = {
    "AI Agents": ["Meme", "Autonomous"],
    "PumpFun": ["Ecosystem", "New"],
    "Solana Memes": ["General", "Blue Chip"],
    "Animals": ["Dogs", "Cats", "Frogs", "Penguins", "Other"],
    "Politics": ["Trump", "General"],
    "Culture": ["Internet", "Celebrities"],
}


def get_all_categories() -> Dict[str, List[str]]:
    """Get all available categories."""
    return TREND_CATEGORIES


def get_keywords_for_category(
    primary_category: str,
    sub_category: Optional[str] = None
) -> List[str]:
    """Get keywords for a category."""
    for (primary, sub), keywords in KEYWORD_CATEGORIES.items():
        if primary == primary_category:
            if sub_category is None or sub == sub_category:
                return keywords
    return []
