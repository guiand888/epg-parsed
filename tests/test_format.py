"""Unit tests for format_episode_num function."""

import pytest
from process_epg import format_episode_num


class TestFormatEpisodeNum:
    """Test format_episode_num function."""

    # With season tests
    def test_with_season_single_digit(self):
        """Test formatting with single digit season and episode."""
        assert format_episode_num("3", "1") == "2.0"

    def test_with_season_double_digit_episode(self):
        """Test formatting with double digit episode."""
        assert format_episode_num("2", "9") == "1.8"

    def test_with_season_double_digit_season(self):
        """Test formatting with double digit season."""
        assert format_episode_num("10", "5") == "9.4"

    def test_with_season_double_digit_both(self):
        """Test formatting with double digit season and episode."""
        assert format_episode_num("15", "25") == "14.24"

    def test_with_season_zero_episode(self):
        """Test formatting with zero episode number (clamped to 0)."""
        assert format_episode_num("1", "0") == "0.0"

    def test_with_season_high_numbers(self):
        """Test formatting with high numbers."""
        assert format_episode_num("99", "999") == "98.998"

    # Without season tests
    def test_without_season(self):
        """Test formatting without season."""
        assert format_episode_num(None, "84") == ".83"

    def test_without_season_high_number(self):
        """Test formatting without season and high episode number."""
        assert format_episode_num(None, "288") == ".287"

    def test_without_season_single_digit(self):
        """Test formatting without season and single digit."""
        assert format_episode_num(None, "5") == ".4"

    # Edge cases
    def test_empty_season_string(self):
        """Test with empty season string - empty string is falsy, uses no-season path."""
        # Empty string is falsy in Python, so if season: is False
        assert format_episode_num("", "1") == ".0"

    def test_zero_season_string(self):
        """Test with zero season as string - non-empty string is truthy, clamped to 0."""
        assert format_episode_num("0", "5") == "0.4"

    def test_string_numbers(self):
        """Test that string numbers are handled correctly."""
        assert format_episode_num("3", "1") == "2.0"
        # int() is called on both season and episode
        assert format_episode_num("05", "09") == "4.8"
