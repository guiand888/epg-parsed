"""Unit tests for download_file function."""

import io
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from process_epg import download_file


class TestDownloadFile:
    """Test download_file function with mocked network calls."""

    def test_successful_download(self, temp_dir):
        """Test successful file download."""
        output_path = temp_dir / "downloaded.xml"
        content = b"test content"
        
        # Create a mock response object
        mock_response = io.BytesIO(content)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = download_file("http://example.com/test.xml", str(output_path))
        
        assert result is True
        assert output_path.exists()
        assert output_path.read_bytes() == content

    def test_download_writes_binary(self, temp_dir):
        """Test that download writes binary content correctly."""
        output_path = temp_dir / "test.xml"
        xml_content = b'<?xml version="1.0"?><tv></tv>'
        
        mock_response = io.BytesIO(xml_content)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = download_file("http://example.com/test.xml", str(output_path))
        
        assert result is True
        assert output_path.read_bytes() == xml_content

    def test_network_error(self, temp_dir):
        """Test download failure due to network error."""
        output_path = temp_dir / "test.xml"
        
        with patch('urllib.request.urlopen', side_effect=URLError("Connection failed")):
            result = download_file("http://invalid.com/test.xml", str(output_path))
        
        assert result is False
        assert not output_path.exists()

    def test_generic_exception(self, temp_dir):
        """Test download failure due to generic exception."""
        output_path = temp_dir / "test.xml"
        
        with patch('urllib.request.urlopen', side_effect=Exception("HTTP 404")):
            result = download_file("http://example.com/notfound.xml", str(output_path))
        
        assert result is False

    def test_empty_content(self, temp_dir):
        """Test download of empty file."""
        output_path = temp_dir / "empty.xml"
        
        mock_response = io.BytesIO(b"")
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = download_file("http://example.com/empty.xml", str(output_path))
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size == 0
