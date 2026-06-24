"""Unit tests for load_config function."""

import json
import pytest
from pathlib import Path
from process_epg import load_config


class TestLoadConfig:
    """Test load_config function with various config files."""

    def test_valid_config(self, temp_dir):
        """Test loading a valid config file."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": [
                {"name": "test", "url": "http://example.com", "output": "out.xml"}
            ]
        }
        config_path.write_text(json.dumps(config_content))
        
        result = load_config(str(config_path))
        assert result == config_content

    def test_valid_config_multiple_sources(self, temp_dir):
        """Test loading a valid config with multiple sources."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "output",
            "sources": [
                {"name": "source1", "url": "http://url1.com", "output": "file1.xml"},
                {"name": "source2", "url": "http://url2.com", "output": "file2.xml"}
            ]
        }
        config_path.write_text(json.dumps(config_content))
        
        result = load_config(str(config_path))
        assert result == config_content
        assert len(result['sources']) == 2

    def test_config_file_not_found(self, capsys):
        """Test loading non-existent config file."""
        with pytest.raises(SystemExit):
            load_config("/nonexistent/path/config.json")
        captured = capsys.readouterr()
        assert "Config file not found" in captured.out

    def test_invalid_json(self, temp_dir, capsys):
        """Test loading config with invalid JSON."""
        config_path = temp_dir / "config.json"
        config_path.write_text("not valid json {")
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.out

    def test_missing_output_dir(self, temp_dir, capsys):
        """Test loading config without output_dir."""
        config_path = temp_dir / "config.json"
        config_content = {"sources": []}
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "output_dir" in captured.out

    def test_missing_sources(self, temp_dir, capsys):
        """Test loading config without sources."""
        config_path = temp_dir / "config.json"
        config_content = {"output_dir": "processed"}
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "sources" in captured.out

    def test_sources_not_list(self, temp_dir, capsys):
        """Test loading config with sources not as a list."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": {"name": "test"}
        }
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "must be a list" in captured.out

    def test_source_missing_name(self, temp_dir, capsys):
        """Test loading config with source missing name field."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": [
                {"url": "http://example.com", "output": "out.xml"}
            ]
        }
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "missing 'name'" in captured.out

    def test_source_missing_url(self, temp_dir, capsys):
        """Test loading config with source missing url field."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": [
                {"name": "test", "output": "out.xml"}
            ]
        }
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "missing 'url'" in captured.out

    def test_source_missing_output(self, temp_dir, capsys):
        """Test loading config with source missing output field."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": [
                {"name": "test", "url": "http://example.com"}
            ]
        }
        config_path.write_text(json.dumps(config_content))
        
        with pytest.raises(SystemExit):
            load_config(str(config_path))
        captured = capsys.readouterr()
        assert "missing 'output'" in captured.out

    def test_empty_sources_list(self, temp_dir):
        """Test loading config with empty sources list (should be valid)."""
        config_path = temp_dir / "config.json"
        config_content = {
            "output_dir": "processed",
            "sources": []
        }
        config_path.write_text(json.dumps(config_content))
        
        result = load_config(str(config_path))
        assert result == config_content
        assert result['sources'] == []
