"""Integration tests for process_all_sources function."""

import shutil
from unittest.mock import patch
from pathlib import Path
from process_epg import process_all_sources


class TestProcessAllSources:
    """Test process_all_sources function with mocked dependencies."""

    def test_single_source_success(self, temp_dir):
        """Test processing a single source successfully."""
        test_xml = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show - EP 5</title>
  </programme>
</tv>'''
        
        test_xml_path = temp_dir / "test_source.xml"
        test_xml_path.write_text(test_xml)
        
        config = {
            "output_dir": "output",
            "sources": [
                {"name": "test", "url": "http://a.test/1", "output": "test_output.xml"}
            ]
        }
        
        def mock_download(url, dest):
            shutil.copy(str(test_xml_path), dest)
            return True
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        assert results['total'] == 1
        assert results['sources']['test']['status'] == 'success'

    def test_multiple_sources_success(self, temp_dir):
        """Test processing multiple sources successfully."""
        xml1 = '''<?xml version="1.0"?>
<tv><programme><title>Show 1 - EP 1</title></programme></tv>'''
        xml2 = '''<?xml version="1.0"?>
<tv><programme><title>Show 2 - EP 2</title></programme></tv>'''
        
        xml1_path = temp_dir / "s1.xml"
        xml2_path = temp_dir / "s2.xml"
        xml1_path.write_text(xml1)
        xml2_path.write_text(xml2)
        
        config = {
            "output_dir": "output",
            "sources": [
                {"name": "s1", "url": "http://a.test/1", "output": "o1.xml"},
                {"name": "s2", "url": "http://b.test/1", "output": "o2.xml"}
            ]
        }
        
        def mock_download(url, dest):
            if "a.test" in url:
                shutil.copy(str(xml1_path), dest)
            else:
                shutil.copy(str(xml2_path), dest)
            return True
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        assert results['total'] == 2
        assert results['sources']['s1']['status'] == 'success'
        assert results['sources']['s2']['status'] == 'success'

    def test_partial_failure_continues(self, temp_dir):
        """Test that processing continues when one source fails."""
        xml_content = '''<?xml version="1.0"?>
<tv><programme><title>Show - EP 1</title></programme></tv>'''
        
        xml_path = temp_dir / "v.xml"
        xml_path.write_text(xml_content)
        
        config = {
            "output_dir": "output",
            "sources": [
                {"name": "good", "url": "http://a.test/g", "output": "g.xml"},
                {"name": "bad", "url": "http://b.test/f", "output": "b.xml"}
            ]
        }
        
        def mock_download(url, dest):
            if "a.test/g" in url:
                shutil.copy(str(xml_path), dest)
                return True
            return False
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        assert results['sources']['good']['status'] == 'success'
        assert results['sources']['bad']['status'] == 'failed'
        assert results['total'] == 1

    def test_creates_output_directory(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        xml_content = '''<?xml version="1.0"?>
<tv><programme><title>Show - EP 1</title></programme></tv>'''
        
        xml_path = temp_dir / "s.xml"
        xml_path.write_text(xml_content)
        
        config = {
            "output_dir": "new_dir",
            "sources": [
                {"name": "t", "url": "http://a.test/1", "output": "t.xml"}
            ]
        }
        
        def mock_download(url, dest):
            shutil.copy(str(xml_path), dest)
            return True
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        output_dir = temp_dir / "new_dir"
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_creates_output_files(self, temp_dir):
        """Test that output files are created in output directory."""
        xml_content = '''<?xml version="1.0"?>
<tv><programme><title>Show - EP 99</title></programme></tv>'''
        
        xml_path = temp_dir / "s.xml"
        xml_path.write_text(xml_content)
        
        config = {
            "output_dir": "out",
            "sources": [
                {"name": "t", "url": "http://a.test/1", "output": "r.xml"}
            ]
        }
        
        def mock_download(url, dest):
            shutil.copy(str(xml_path), dest)
            return True
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        output_file = temp_dir / "out" / "r.xml"
        assert output_file.exists()

    def test_empty_sources_list(self, temp_dir):
        """Test processing with empty sources list."""
        config = {
            "output_dir": "output",
            "sources": []
        }
        
        with patch('process_epg.download_file', return_value=True):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        assert results['total'] == 0
        assert results['sources'] == {}

    def test_result_structure(self, temp_dir):
        """Test that results have correct structure."""
        xml_content = '''<?xml version="1.0"?>
<tv><programme><title>Show - EP 5</title></programme></tv>'''
        
        xml_path = temp_dir / "s.xml"
        xml_path.write_text(xml_content)
        
        config = {
            "output_dir": "out",
            "sources": [
                {"name": "t", "url": "http://a.test/1", "output": "t.xml"}
            ]
        }
        
        def mock_download(url, dest):
            shutil.copy(str(xml_path), dest)
            return True
        
        with patch('process_epg.download_file', side_effect=mock_download):
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(str(temp_dir))
                results = process_all_sources(config)
            finally:
                os.chdir(str(original_cwd))
        
        assert 'total' in results
        assert 'sources' in results
        assert isinstance(results['total'], int)
        assert isinstance(results['sources'], dict)
        assert 't' in results['sources']
        assert 'status' in results['sources']['t']
        assert 'processed' in results['sources']['t']
        assert 'output' in results['sources']['t']
