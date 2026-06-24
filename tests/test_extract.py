"""Unit tests for extract_episode_info function."""

import pytest
from process_epg import extract_episode_info


class TestExtractEpisodeInfo:
    """Test extract_episode_info function with various patterns."""

    # SX - EP pattern tests
    def test_sx_ep_pattern_basic(self):
        """Test basic SX - EP pattern."""
        title, season, episode = extract_episode_info("Show S3 - EP 1")
        assert title == "Show"
        assert season == "3"
        assert episode == "1"

    def test_sx_ep_pattern_with_colon(self):
        """Test SX - EP pattern with colon in title."""
        title, season, episode = extract_episode_info("CSI: Vegas S3 - EP 1")
        assert title == "CSI: Vegas"
        assert season == "3"
        assert episode == "1"

    def test_sx_ep_pattern_with_spaces(self):
        """Test SX - EP pattern with multiple spaces."""
        title, season, episode = extract_episode_info("My Show  S2 - EP 5")
        assert title == "My Show"
        assert season == "2"
        assert episode == "5"

    def test_sx_ep_pattern_double_digit_season(self):
        """Test SX - EP pattern with double digit season."""
        title, season, episode = extract_episode_info("Show S10 - EP 25")
        assert title == "Show"
        assert season == "10"
        assert episode == "25"

    # SrX - EP pattern tests
    def test_srx_ep_pattern(self):
        """Test SrX - EP pattern."""
        title, season, episode = extract_episode_info("Show Sr2 - EP 9")
        assert title == "Show"
        assert season == "2"
        assert episode == "9"

    def test_srx_ep_pattern_with_colon(self):
        """Test SrX - EP pattern with colon - non-greedy match stops at first separator."""
        title, season, episode = extract_episode_info("Show: Sr3 - EP 15")
        # The non-greedy (.+?) matches "Show" and then [\s:]+ matches ": " before "Sr3"
        assert title == "Show"
        assert season == "3"
        assert episode == "15"

    # Season X - EP pattern tests
    def test_season_ep_pattern(self):
        """Test Season X - EP pattern."""
        title, season, episode = extract_episode_info("Show Season 02 - EP 7")
        assert title == "Show"
        assert season == "02"
        assert episode == "7"

    def test_season_ep_pattern_with_colon(self):
        """Test Season X - EP pattern with colon - non-greedy match."""
        title, season, episode = extract_episode_info("Show: Season 2 - EP 10")
        # The non-greedy (.+?) matches "Show" and then [\s:]+ matches ": " before "Season"
        assert title == "Show"
        assert season == "2"
        assert episode == "10"

    def test_season_ep_pattern_full(self):
        """Test Season X - EP pattern with full word and colon."""
        title, season, episode = extract_episode_info("Raid The Cage: Season 02 - EP 7")
        # The non-greedy (.+?) matches "Raid The Cage" and then [\s:]+ matches ": " before "Season"
        assert title == "Raid The Cage"
        assert season == "02"
        assert episode == "7"

    # Paren - EP pattern tests
    def test_paren_ep_pattern(self):
        """Test parenthetical - EP pattern."""
        title, season, episode = extract_episode_info("Show (text) - EP 2028")
        # The pattern captures everything before the first '(' as group 1
        # But actually the pattern is: ^(.+?)\(.*?\)\s+-\s+EP\s+(\d+)$
        # The non-greedy (.+?) matches "Show " and then \(.*?\) matches "(text)"
        # So group 1 is "Show " which gets stripped to "Show"
        # But wait, the regex is: ^(.+?)\(.*?\)\s+-\s+EP\s+(\d+)$
        # (.+?) matches as little as possible, then \(.*?\) matches the parenthetical
        # So for "Show (text) - EP 2028", (.+?) matches "Show" and \(.*?\) matches "(text)"
        # Then \s+ matches " " before "-"
        assert title == "Show"
        assert season is None
        assert episode == "2028"

    def test_paren_ep_pattern_complex(self):
        """Test complex parenthetical - EP pattern."""
        title, season, episode = extract_episode_info("Lo and Behold (Ep1,868 - 2,243) - EP 2028")
        # Similar to above, (.+?) matches "Lo and Behold " and \(.*?\) matches "(Ep1,868 - 2,243)"
        # After stripping, we get "Lo and Behold"
        assert title == "Lo and Behold"
        assert season is None
        assert episode == "2028"

    # Simple EP pattern tests
    def test_simple_ep_pattern(self):
        """Test simple - EP pattern."""
        title, season, episode = extract_episode_info("Show - EP 84")
        assert title == "Show"
        assert season is None
        assert episode == "84"

    def test_simple_ep_pattern_high_number(self):
        """Test simple - EP pattern with high episode number."""
        title, season, episode = extract_episode_info("Headline News - EP 288")
        assert title == "Headline News"
        assert season is None
        assert episode == "288"

    # No EP pattern tests
    def test_no_ep_pattern(self):
        """Test title without EP pattern."""
        title, season, episode = extract_episode_info("Show")
        assert title == "Show"
        assert season is None
        assert episode is None

    def test_no_ep_pattern_with_description(self):
        """Test title without EP pattern but with description."""
        title, season, episode = extract_episode_info("Show without EP")
        assert title == "Show without EP"
        assert season is None
        assert episode is None

    def test_empty_title(self):
        """Test empty title."""
        title, season, episode = extract_episode_info("")
        assert title == ""
        assert season is None
        assert episode is None

    def test_just_ep(self):
        """Test title that is just EP number - pattern requires show name before EP."""
        title, season, episode = extract_episode_info("EP 1")
        assert title == "EP 1"
        assert season is None
        assert episode is None

    # Case insensitivity tests
    def test_lowercase_ep(self):
        """Test lowercase ep."""
        title, season, episode = extract_episode_info("Show - ep 5")
        assert title == "Show"
        assert season is None
        assert episode == "5"

    def test_mixed_case_sx(self):
        """Test mixed case SX."""
        title, season, episode = extract_episode_info("Show s3 - Ep 1")
        assert title == "Show"
        assert season == "3"
        assert episode == "1"

    def test_uppercase_sx(self):
        """Test uppercase SX."""
        title, season, episode = extract_episode_info("Show S3 - EP 1")
        assert title == "Show"
        assert season == "3"
        assert episode == "1"
