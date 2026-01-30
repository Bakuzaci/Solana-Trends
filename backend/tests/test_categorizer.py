"""Tests for the categorizer service."""
import pytest
from app.services.categorizer import categorize_token, get_all_categories, get_category_emoji


class TestTokenCategorizer:
    """Test the token categorizer."""

    def test_categorize_animal_token(self):
        """Test categorizing animal-themed tokens."""
        # Test dog-related token
        category, sub_category, keywords = categorize_token("DOGE", "Dogecoin")
        assert category == "Animals"
        assert sub_category == "Dogs"
        assert len(keywords) > 0

        # Test cat-related token
        category, sub_category, keywords = categorize_token("CAT", "Cat Token")
        assert category == "Animals"
        assert sub_category == "Cats"

    def test_categorize_meme_token(self):
        """Test categorizing meme-themed tokens."""
        category, sub_category, keywords = categorize_token("PEPE", "Pepe Coin")
        assert category in ["Meme Culture", "Animals"]  # Could match Frogs or Classic Memes
        assert len(keywords) > 0

    def test_categorize_tech_token(self):
        """Test categorizing tech-themed tokens."""
        category, sub_category, keywords = categorize_token("GPT", "ChatGPT AI")
        assert category == "Technology"
        assert sub_category == "AI & Bots"
        assert "gpt" in keywords or "chat" in keywords

    def test_categorize_unknown_token(self):
        """Test categorizing unknown tokens."""
        category, sub_category, keywords = categorize_token("XYZ123", "Random Token")
        # Should return None for unknown tokens
        assert category is None or category in get_all_categories()

    def test_get_all_categories(self):
        """Test getting all categories."""
        categories = get_all_categories()
        assert isinstance(categories, dict)
        assert "Animals" in categories
        assert "Technology" in categories
        assert "Meme Culture" in categories

    def test_get_category_emoji(self):
        """Test getting category emojis."""
        emoji = get_category_emoji("Animals", "Dogs")
        assert emoji == "🐕"

        emoji = get_category_emoji("Technology")
        assert emoji == "💻"
