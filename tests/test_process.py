"""Integration tests for process_epg function."""

import xml.etree.ElementTree as ET
from pathlib import Path
from process_epg import process_epg


class TestProcessEpg:
    """Test process_epg function with real XML files."""

    def test_process_single_programme(self, temp_dir, create_xml_file):
        """Test processing XML with single programme."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Test Show S1 - EP 5</title>
    <desc>Test description</desc>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 1
        assert output_path.exists()
        
        # Verify episode-num element was added
        tree = ET.parse(str(output_path))
        episode_elem = tree.find('.//episode-num')
        assert episode_elem is not None
        assert episode_elem.text == "0.4"
        assert episode_elem.get('system') == 'xmltv_ns'

    def test_process_multiple_programmes(self, temp_dir, create_xml_file):
        """Test processing XML with multiple programmes."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show One S3 - EP 1</title>
    <desc>First</desc>
  </programme>
  <programme>
    <title>Show Two Season 02 - EP 7</title>
    <desc>Second</desc>
  </programme>
  <programme>
    <title>Show Three - EP 42</title>
    <desc>Third</desc>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 3
        
        # Verify all episode-num elements
        tree = ET.parse(str(output_path))
        episodes = tree.findall('.//episode-num')
        assert len(episodes) == 3
        assert episodes[0].text == "2.0"
        assert episodes[1].text == "1.6"
        assert episodes[2].text == ".41"

    def test_process_with_non_episode_programmes(self, temp_dir, create_xml_file):
        """Test processing XML with mixed programmes (some with episodes, some without)."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show One - EP 5</title>
    <desc>Has episode</desc>
  </programme>
  <programme>
    <title>Show Two</title>
    <desc>No episode</desc>
  </programme>
  <programme>
    <title>Show Three S2 - EP 10</title>
    <desc>Has episode</desc>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 2  # Only 2 programmes have EP pattern
        
        # Verify only programmes with EP have episode-num
        tree = ET.parse(str(output_path))
        programmes = tree.findall('.//programme')
        assert len(programmes) == 3
        
        # Check first programme has episode-num
        assert programmes[0].find('episode-num') is not None
        # Check second programme does NOT have episode-num
        assert programmes[1].find('episode-num') is None
        # Check third programme has episode-num
        assert programmes[2].find('episode-num') is not None

    def test_process_preserves_other_elements(self, temp_dir, create_xml_file):
        """Test that processing preserves other XML elements."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show S1 - EP 5</title>
    <desc>Description</desc>
    <icon src="http://example.com/icon.png"/>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        process_epg(str(input_path), str(output_path))
        
        # Parse and verify all elements preserved
        tree = ET.parse(str(output_path))
        programme = tree.find('.//programme')
        
        assert programme.find('title') is not None
        assert programme.find('desc') is not None
        assert programme.find('icon') is not None
        assert programme.find('episode-num') is not None

    def test_process_empty_xml(self, temp_dir, create_xml_file):
        """Test processing XML with no programmes."""
        xml_content = '''<?xml version="1.0"?>
<tv>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 0
        assert output_path.exists()

    def test_process_programme_without_title(self, temp_dir, create_xml_file):
        """Test processing XML with programme missing title element."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <desc>No title</desc>
  </programme>
  <programme>
    <title>Show - EP 5</title>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 1  # Only the second programme has title and EP

    def test_process_programme_with_none_title_text(self, temp_dir, create_xml_file):
        """Test processing XML with programme having title element but None text."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title></title>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        count = process_epg(str(input_path), str(output_path))
        
        assert count == 0

    def test_process_episode_num_position(self, temp_dir, create_xml_file):
        """Test that episode-num is inserted after title."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show S1 - EP 5</title>
    <desc>Description</desc>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        process_epg(str(input_path), str(output_path))
        
        # Parse and check element order
        tree = ET.parse(str(output_path))
        programme = tree.find('.//programme')
        elements = list(programme)
        
        # Find indices
        title_idx = next(i for i, elem in enumerate(elements) if elem.tag == 'title')
        ep_idx = next(i for i, elem in enumerate(elements) if elem.tag == 'episode-num')
        desc_idx = next(i for i, elem in enumerate(elements) if elem.tag == 'desc')
        
        # episode-num should be after title but before desc
        assert ep_idx == title_idx + 1
        assert ep_idx < desc_idx

    def test_process_xml_declaration(self, temp_dir, create_xml_file):
        """Test that output XML has proper declaration."""
        xml_content = '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show - EP 1</title>
  </programme>
</tv>'''
        
        input_path = create_xml_file(xml_content)
        output_path = temp_dir / "output.xml"
        
        process_epg(str(input_path), str(output_path))
        
        # Read raw content to check declaration
        content = output_path.read_text()
        assert content.startswith('<?xml version=')
        assert 'encoding=' in content
