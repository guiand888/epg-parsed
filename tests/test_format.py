"""Unit tests for format_episode_num function."""

import pytest
from process_epg import format_episode_num


class TestFormatEpisodeNum:
    """Test format_episode_num function."""

    # With season tests
    def test_with_season_single_digit(self):
        """Test formatting with single digit season and episode."""
        assert format_episode_num("3", "1") == "3.01"

    def test_with_season_double_digit_episode(self):
        """Test formatting with double digit episode."""
        assert format_episode_num("2", "9") == "2.09"

    def test_with_season_double_digit_season(self):
        """Test formatting with double digit season."""
        assert format_episode_num("10", "5") == "10.05"

    def test_with_season_double_digit_both(self):
        """Test formatting with double digit season and episode."""
        assert format_episode_num("15", "25") == "15.25"

    def test_with_season_zero_episode(self):
        """Test formatting with zero episode number."""
        assert format_episode_num("1", "0") == "1.00"

    def test_with_season_high_numbers(self):
        """Test formatting with high numbers."""
        assert format_episode_num("99", "999") == "99.999"

    # Without season tests
    def test_without_season(self):
        """Test formatting without season."""
        assert format_episode_num(None, "84") == "84"

    def test_without_season_high_number(self):
        """Test formatting without season and high episode number."""
        assert format_episode_num(None, "288") == "288"

    def test_without_season_single_digit(self):
        """Test formatting without season and single digit."""
        assert format_episode_num(None, "5") == "5"

    # Edge cases
    def test_empty_season_string(self):
        """Test with empty season string - empty string is falsy, returns episode only."""
        # Empty string is falsy in Python, so if season: is False
        assert format_episode_num("", "1") == "1"

    def test_zero_season_string(self):
        """Test with zero season as string - non-empty string is truthy."""
        assert format_episode_num("0", "5") == "0.05"

    def test_string_numbers(self):
        """Test that string numbers are handled correctly."""
        assert format_episode_num("3", "1") == "3.01"
        # This should work since int() is called on episode
        assert format_episode_num("05", "09") == "05.09"
