"""
Token categorization service using fuzzy string matching.

Categorizes Solana meme coins based on name/symbol patterns
using rapidfuzz for fuzzy matching. Includes emoji mapping
for visual category identification.
"""
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process


# =============================================================================
# Category Emoji Mapping
# =============================================================================

CATEGORY_EMOJIS: Dict[str, Dict[str, str]] = {
    "Animals": {
        "_default": "🐾",
        "Dogs": "🐕",
        "Cats": "🐱",
        "Frogs": "🐸",
        "Monkeys": "🐵",
        "Birds": "🦅",
        "Other Animals": "🦁",
    },
    "Meme Culture": {
        "_default": "😂",
        "Classic Memes": "🐸",
        "Internet Culture": "💀",
        "Emoji Culture": "🔥",
    },
    "Pop Culture": {
        "_default": "⭐",
        "Celebrities": "🌟",
        "Movies & TV": "🎬",
        "Anime": "🎌",
        "Gaming": "🎮",
    },
    "Finance": {
        "_default": "💰",
        "Trading": "📈",
        "DeFi": "🏦",
        "Crypto Culture": "₿",
    },
    "Technology": {
        "_default": "💻",
        "AI & Bots": "🤖",
        "Tech Companies": "🏢",
        "Futurism": "🚀",
    },
    "Food & Lifestyle": {
        "_default": "🍕",
        "Food": "🍔",
        "Lifestyle": "💎",
    },
    "Politics": {
        "_default": "🏛️",
        "Political": "🗳️",
        "Social Issues": "✊",
    },
    "Miscellaneous": {
        "_default": "✨",
        "Numbers & Symbols": "🔢",
        "Abstract": "🌌",
        "Random": "🎲",
    },
}


def get_category_emoji(primary_category: str, sub_category: Optional[str] = None) -> str:
    """
    Get the emoji for a category.

    Args:
        primary_category: The primary category name
        sub_category: Optional sub-category name

    Returns:
        Emoji string for the category
    """
    if primary_category not in CATEGORY_EMOJIS:
        return "📊"

    category_emojis = CATEGORY_EMOJIS[primary_category]

    if sub_category and sub_category in category_emojis:
        return category_emojis[sub_category]

    return category_emojis.get("_default", "📊")


# =============================================================================
# Trend Categories Dictionary
# =============================================================================

TREND_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    # Animals & Creatures
    "Animals": {
        "Dogs": [
            "dog", "doge", "shiba", "inu", "puppy", "pup", "woof", "bark",
            "corgi", "bulldog", "poodle", "husky", "retriever", "chihuahua"
        ],
        "Cats": [
            "cat", "kitty", "kitten", "meow", "feline", "whiskers", "tabby",
            "persian", "siamese", "nyan"
        ],
        "Frogs": [
            "frog", "pepe", "toad", "ribbit", "kermit", "tadpole", "amphibian"
        ],
        "Monkeys": [
            "monkey", "ape", "chimp", "gorilla", "banana", "primate", "orangutan",
            "baboon", "macaque"
        ],
        "Birds": [
            "bird", "eagle", "owl", "crow", "raven", "penguin", "parrot",
            "hawk", "falcon", "tweet", "chirp"
        ],
        "Other Animals": [
            "bear", "bull", "lion", "tiger", "wolf", "fox", "rabbit", "bunny",
            "elephant", "whale", "shark", "fish", "dragon", "unicorn", "pig",
            "hamster", "rat", "mouse", "snake", "lizard", "turtle"
        ],
    },

    # Meme Culture
    "Meme Culture": {
        "Classic Memes": [
            "pepe", "wojak", "chad", "virgin", "doge", "nyan", "troll",
            "stonks", "hodl", "rekt", "fomo", "fud", "ngmi", "gmi", "wagmi"
        ],
        "Internet Culture": [
            "based", "cringe", "cope", "seethe", "ratio", "sus", "mid",
            "bussin", "cap", "nocap", "simp", "stan", "yeet", "vibe"
        ],
        "Emoji Culture": [
            "moon", "rocket", "fire", "100", "diamond", "hands", "gem",
            "crown", "skull", "clown", "brain"
        ],
    },

    # Pop Culture
    "Pop Culture": {
        "Celebrities": [
            "elon", "musk", "trump", "biden", "kanye", "drake", "snoop",
            "rihanna", "taylor", "swift", "kardashian", "bieber"
        ],
        "Movies & TV": [
            "marvel", "disney", "star", "wars", "trek", "matrix", "batman",
            "superman", "joker", "thanos", "avengers", "game", "thrones"
        ],
        "Anime": [
            "anime", "manga", "waifu", "senpai", "kawaii", "otaku", "naruto",
            "goku", "dbz", "pokemon", "pikachu", "sailor"
        ],
        "Gaming": [
            "game", "gamer", "xbox", "playstation", "nintendo", "mario",
            "zelda", "minecraft", "fortnite", "roblox", "esports", "twitch"
        ],
    },

    # Finance & Crypto
    "Finance": {
        "Trading": [
            "pump", "dump", "moon", "lambo", "hodl", "whale", "dip", "ath",
            "bull", "bear", "short", "long", "leverage", "margin"
        ],
        "DeFi": [
            "defi", "yield", "farm", "stake", "swap", "liquidity", "pool",
            "apy", "apr", "vault", "protocol"
        ],
        "Crypto Culture": [
            "bitcoin", "btc", "eth", "sol", "crypto", "blockchain", "nft",
            "web3", "metaverse", "dao", "token"
        ],
    },

    # Tech & AI
    "Technology": {
        "AI & Bots": [
            # General AI terms
            "ai", "gpt", "bot", "robot", "neural", "machine", "learning",
            "chat", "assistant", "agent", "llm", "openai", "claude", "gemini",
            "autonomous", "artificial", "intelligence",
            # Hot AI agent tokens
            "clawd", "claw", "openclaw", "molt", "moltbot",
            "ai16z", "eliza", "elizaos", "degenai",
            "zerebro", "hyperstition",
            "griffain", "griffin",
            "arc", "rig",
            "goat", "goatseus", "maximus", "truth", "terminal",
            "virtuals", "virtual", "protocol",
        ],
        "Tech Companies": [
            "apple", "google", "meta", "microsoft", "amazon", "tesla",
            "nvidia", "amd", "intel"
        ],
        "Futurism": [
            "cyber", "quantum", "nano", "space", "mars", "rocket", "future",
            "virtual", "digital", "matrix"
        ],
    },

    # Food & Lifestyle
    "Food & Lifestyle": {
        "Food": [
            "pizza", "burger", "taco", "sushi", "ramen", "bacon", "cheese",
            "coffee", "beer", "wine", "whiskey", "chocolate", "cookie"
        ],
        "Lifestyle": [
            "rich", "luxury", "gold", "diamond", "yacht", "lambo", "ferrari",
            "rolex", "gucci", "supreme"
        ],
    },

    # Politics & Society
    "Politics": {
        "Political": [
            "trump", "biden", "maga", "democrat", "republican", "liberal",
            "conservative", "freedom", "liberty", "patriot"
        ],
        "Social Issues": [
            "green", "climate", "peace", "love", "unity", "equality",
            "justice", "community"
        ],
    },

    # Miscellaneous
    "Miscellaneous": {
        "Numbers & Symbols": [
            "420", "69", "100", "1000x", "10x", "infinite", "zero", "one",
            "million", "billion", "trillion"
        ],
        "Abstract": [
            "moon", "sun", "star", "cosmic", "galaxy", "universe", "infinite",
            "eternal", "genesis", "alpha", "omega", "prime"
        ],
        "Random": [
            "yolo", "lol", "wtf", "omg", "bruh", "bro", "dude", "guy",
            "thing", "stuff", "random"
        ],
    },
}


# Flatten categories for quick keyword lookup
def _build_keyword_index() -> Dict[str, Tuple[str, str]]:
    """Build a reverse index from keywords to categories."""
    index = {}
    for primary_cat, sub_cats in TREND_CATEGORIES.items():
        for sub_cat, keywords in sub_cats.items():
            for keyword in keywords:
                # Store the first match for each keyword
                if keyword.lower() not in index:
                    index[keyword.lower()] = (primary_cat, sub_cat)
    return index


KEYWORD_INDEX = _build_keyword_index()

# Flatten all keywords for fuzzy matching
ALL_KEYWORDS = list(KEYWORD_INDEX.keys())


def categorize_token(
    name: str,
    symbol: str,
    confidence_threshold: int = 90
) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Categorize a token based on its name and symbol.

    Uses EXACT matching only - fuzzy matching was too loose and caused
    wrong categorizations (e.g., "TULSA" matching "tweet" -> Birds).

    Args:
        name: Token name
        symbol: Token symbol
        confidence_threshold: Unused, kept for API compatibility.

    Returns:
        Tuple of (primary_category, sub_category, detected_keywords)
        Returns (None, None, []) if no match found.
    """
    # Clean and tokenize the name/symbol
    combined_text = f"{name} {symbol}".lower()
    
    # Remove common noise
    noise_words = {'token', 'coin', 'sol', 'solana', 'the', 'of', 'a', 'an'}
    
    # Extract words (alphanumeric only)
    import re
    words = set(re.findall(r'[a-z0-9]+', combined_text))
    words = words - noise_words
    
    # Track matches with priority (longer keyword matches = better)
    detected_keywords = []
    best_match: Optional[Tuple[str, str, int]] = None  # (primary, sub, keyword_length)

    # ONLY exact matching - no fuzzy
    for keyword, (primary_cat, sub_cat) in KEYWORD_INDEX.items():
        keyword_lower = keyword.lower()
        
        # Method 1: Exact word match (highest priority)
        if keyword_lower in words:
            detected_keywords.append(keyword)
            # Prefer longer keywords (more specific)
            if best_match is None or len(keyword) > best_match[2]:
                best_match = (primary_cat, sub_cat, len(keyword))
            continue
        
        # Method 2: Substring match only for keywords >= 4 chars
        # This catches things like "dogwifhat" containing "dog"
        if len(keyword) >= 4 and keyword_lower in combined_text:
            detected_keywords.append(keyword)
            if best_match is None or len(keyword) > best_match[2]:
                best_match = (primary_cat, sub_cat, len(keyword))

    if best_match:
        return best_match[0], best_match[1], detected_keywords

    return None, None, detected_keywords


def get_all_categories() -> Dict[str, List[str]]:
    """
    Get all available categories and their sub-categories.

    Returns:
        Dictionary mapping primary categories to lists of sub-categories.
    """
    return {
        primary: list(subs.keys())
        for primary, subs in TREND_CATEGORIES.items()
    }


def get_keywords_for_category(
    primary_category: str,
    sub_category: Optional[str] = None
) -> List[str]:
    """
    Get all keywords for a specific category.

    Args:
        primary_category: The primary category name
        sub_category: Optional sub-category name

    Returns:
        List of keywords for the specified category
    """
    if primary_category not in TREND_CATEGORIES:
        return []

    if sub_category:
        return TREND_CATEGORIES[primary_category].get(sub_category, [])

    # Return all keywords for the primary category
    all_keywords = []
    for sub_cat_keywords in TREND_CATEGORIES[primary_category].values():
        all_keywords.extend(sub_cat_keywords)
    return all_keywords
