import pytest
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


@pytest.fixture
def temp_dir():
    """Create and clean up temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_xml_content():
    """Provide sample XML content for testing."""
    return '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Test Show S1 - EP 5</title>
    <desc>Test description</desc>
  </programme>
</tv>'''


@pytest.fixture
def sample_xml_with_multiple_shows():
    """Provide sample XML with multiple programmes."""
    return '''<?xml version="1.0"?>
<tv>
  <programme>
    <title>Show One S3 - EP 1</title>
    <desc>First show</desc>
  </programme>
  <programme>
    <title>Show Two Season 02 - EP 7</title>
    <desc>Second show</desc>
  </programme>
  <programme>
    <title>Show Three - EP 42</title>
    <desc>Third show</desc>
  </programme>
  <programme>
    <title>No Episode Here</title>
    <desc>Fourth show without episode</desc>
  </programme>
</tv>'''


@pytest.fixture
def create_xml_file(temp_dir):
    """Create XML file in temp directory with given content."""
    def _create(content):
        xml_file = temp_dir / "test.xml"
        xml_file.write_text(content)
        return xml_file
    return _create
