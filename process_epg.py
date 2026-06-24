#!/usr/bin/env python3
"""EPG Processor for Emby Live TV Plugin

Extracts episode numbers from StarHub TV EPG and adds XMLTV metadata.

Usage:
    python process_epg.py <input_xml> <output_xml>
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Episode number patterns (most specific first)
# Note: Patterns must handle colons, spaces, and other punctuation in titles
SX_EP = re.compile(r'^(.+?)[\s:]+S(\d+)\s+-\s+EP\s+(\d+)$', re.IGNORECASE)
SRX_EP = re.compile(r'^(.+?)[\s:]+Sr(\d+)\s+-\s+EP\s+(\d+)$', re.IGNORECASE)
SEASON_EP = re.compile(r'^(.+?)[\s:]+Season\s+(\d+)\s+-\s+EP\s+(\d+)$', re.IGNORECASE)
PAREN_EP = re.compile(r'^(.+?)\(.*?\)\s+-\s+EP\s+(\d+)$', re.IGNORECASE)
EP = re.compile(r'^(.+?)\s+-\s+EP\s+(\d+)$', re.IGNORECASE)


def extract_episode_info(title):
    """
    Extract episode information from title.
    Returns: (clean_title, season, episode) or (title, None, None)
    """
    # Try patterns in order from most specific to least
    for pattern, has_season in [
        (SX_EP, True),
        (SRX_EP, True),
        (SEASON_EP, True),
        (PAREN_EP, False),
        (EP, False),
    ]:
        m = pattern.match(title)
        if m:
            if has_season:
                return m.group(1).strip(), m.group(2), m.group(3)
            else:
                # For patterns without season, episode is the last group
                groups = m.groups()
                return groups[0].strip(), None, groups[-1]
    return title, None, None


def format_episode_num(season, episode):
    """Format episode number for xmltv_ns system."""
    if season:
        return f"{season}.{int(episode):02d}"
    return episode


def process_epg(input_path, output_path):
    """Process EPG XML file."""
    tree = ET.parse(input_path)
    root = tree.getroot()
    processed = 0

    for programme in root.findall('.//programme'):
        title_elem = programme.find('title')
        if title_elem is None or title_elem.text is None:
            continue

        title = title_elem.text.strip()
        _, season, episode = extract_episode_info(title)

        if episode:
            # Add episode-num element after title
            ep_num = format_episode_num(season, episode)
            ep_elem = ET.Element('episode-num')
            ep_elem.set('system', 'xmltv_ns')
            ep_elem.text = ep_num

            # Insert after title
            idx = list(programme).index(title_elem)
            programme.insert(idx + 1, ep_elem)
            processed += 1

            if processed <= 3:
                print(f"  Example: '{title}' -> episode-num: {ep_num}")

    # Write output with proper XML declaration
    tree.write(output_path, encoding='UTF-8', xml_declaration=True)
    print(f"Processed {processed} programmes. Output: {output_path}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_xml> <output_xml>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(input_path).exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Processing {input_path}...")
    process_epg(input_path, output_path)
    print("Done!")


if __name__ == '__main__':
    main()
