#!/usr/bin/env python3
"""EPG Processor for Emby Live TV Plugin

Extracts episode numbers from StarHub TV EPG and adds XMLTV metadata.
Supports multiple sources via config file.

Usage:
    python process_epg.py [--config CONFIG_FILE]

Configuration:
    See config.json for source definitions and output directory.

Output-format notes (why the serialiser is the way it is):
    The processed feed is consumed by Emby Live TV, which uses a strict XMLTV
    parser that rejects whitespace-only text nodes sitting between elements and
    chokes on empty <desc/> elements. An earlier version used
    xml.dom.minidom.toprettyxml, which injected a whitespace text node between
    every child element and produced ~35k blank lines in a 7k-programme feed;
    Emby then failed to read the file entirely (showed nothing). The current
    pipeline therefore (1) emits a compact document with no blank lines and no
    stray whitespace text nodes, (2) keeps the original episode suffix in the
    title so the human-readable name is preserved for every consumer, and
    (3) carries the structured metadata in a full 3-part xmltv_ns
    <episode-num> element (season.episode.part), which is what Emby expects.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET

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


def format_episode_num(season, episode, indexing="zero"):
    """Format episode number for the xmltv_ns system.

    Returns the FULL 3-part 'season.episode.part' form (e.g. "5.4.0" or
    ".101.0"). The third component (part) is always "0" because the source
    feed has no part information. Emby expects the complete 3-part form; the
    earlier 2-part output (e.g. "5.4") was rejected/misread by Emby.

    Indexing: the xmltv_ns spec defines season/episode as 0-based, so the
    default `indexing="zero"` subtracts 1 from the 1-based numbers found in
    the source titles (e.g. "S6 - EP 5" -> "5.4.0"). Use "one" only if a
    particular consumer expects 1-based values.

    `indexing` is 'zero' (default, spec-correct) or 'one' (1-indexed).
    """
    if indexing == "one":
        s = int(season) if season else None
        e = int(episode)
    else:
        s = max(0, int(season) - 1) if season else None
        e = max(0, int(episode) - 1)

    if s is not None:
        return f"{s}.{e}.0"
    return f".{e}.0"


def _clean_whitespace(elem):
    """Recursively clear whitespace-only .text/.tail on every element.

    ElementTree only writes a child's .tail *after* the child closes, so any
    whitespace we leave there becomes a whitespace text node between siblings.
    Emby's strict XMLTV parser rejects those nodes, so we null them out before
    serialising. (The remaining top-level blank lines are stripped separately
    in process_epg after ET.indent.)
    """
    for child in elem:
        if child.text is not None and child.text.strip() == "":
            child.text = None
        if child.tail is not None and child.tail.strip() == "":
            child.tail = None
        _clean_whitespace(child)
    if elem.tail is not None and elem.tail.strip() == "":
        elem.tail = None


def process_epg(input_path, output_path, indexing="zero"):
    """Process an EPG XML file: add xmltv_ns <episode-num> metadata.

    Key behaviour (chosen to keep Emby Live TV happy while not breaking other
    consumers such as Dispatcharr):
      * The episode suffix in the title is PRESERVED (we no longer strip
        "S6 - EP 5" down to "FBI"). Both Emby and Dispatcharr then keep the
        readable name; the structured data lives in <episode-num> only.
      * Empty <desc/> elements are removed: Emby is sensitive to them and they
        carry no information.
      * Output is serialised with no blank lines and no whitespace-only text
        nodes between elements (see _clean_whitespace + the blank-line strip
        below). This is the fix for Emby failing to parse the feed at all.
    """
    tree = ET.parse(input_path)
    root = tree.getroot()
    processed = 0

    for programme in root.findall('.//programme'):
        # Drop empty <desc> elements: Emby is sensitive to empty elements and
        # they carry no useful information.
        for desc in programme.findall('desc'):
            if desc.text is None or desc.text.strip() == "":
                programme.remove(desc)

        title_elem = programme.find('title')
        if title_elem is None or title_elem.text is None:
            continue

        title = title_elem.text.strip()
        # extract_episode_info returns a cleaned title too, but we intentionally
        # KEEP the original title text (with its episode suffix) for consumers
        # that read the title directly. The suffix is only used to derive
        # <episode-num> below.
        clean_title, season, episode = extract_episode_info(title)

        if episode and programme.find('episode-num') is None:
            # Add a full 3-part xmltv_ns episode-num right after the title.
            ep_num = format_episode_num(season, episode, indexing=indexing)
            ep_elem = ET.Element('episode-num')
            ep_elem.set('system', 'xmltv_ns')
            ep_elem.text = ep_num

            # Insert immediately after title (keeps the title as the first
            # child, which is the conventional XMLTV ordering).
            idx = list(programme).index(title_elem)
            programme.insert(idx + 1, ep_elem)

            processed += 1

    # Remove any whitespace-only text/tail so the serialised output has no
    # stray whitespace text nodes between elements (these break Emby's parser).
    _clean_whitespace(root)

    # Serialise with indentation for readability, but then strip every blank
    # line: ET.indent leaves whitespace-only tail text between top-level
    # elements (e.g. between </channel> and the next <channel>), which would
    # otherwise produce empty lines that some strict parsers dislike.
    ET.indent(root, space='  ')
    body = ET.tostring(root, encoding='unicode')
    body = "\n".join(line for line in body.splitlines() if line.strip() != "")

    with open(output_path, 'w', encoding='UTF-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(body)
    return processed


def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
            with open(dest_path, 'wb') as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def load_config(config_path):
    """
    Load and validate configuration file.
    
    Returns: config dict
    Raises: SystemExit on validation errors
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)

    # Validate required fields
    if 'output_dir' not in config:
        print("Error: Config file must contain 'output_dir'")
        sys.exit(1)
    
    if 'sources' not in config:
        print("Error: Config file must contain 'sources'")
        sys.exit(1)
    
    if not isinstance(config['sources'], list):
        print("Error: 'sources' must be a list")
        sys.exit(1)
    
    # Validate each source
    for i, source in enumerate(config['sources']):
        if 'name' not in source:
            print(f"Error: Source {i} missing 'name' field")
            sys.exit(1)
        if 'url' not in source:
            print(f"Error: Source {i} ({source.get('name', '?')}) missing 'url' field")
            sys.exit(1)
        if 'output' not in source:
            print(f"Error: Source {i} ({source.get('name', '?')}) missing 'output' field")
            sys.exit(1)

    seen = set()
    for source in config['sources']:
        if source['name'] in seen:
            print(f"Error: Duplicate source name: '{source['name']}'")
            sys.exit(1)
        seen.add(source['name'])

    return config


def process_all_sources(config):
    """
    Process all sources defined in config.

    Returns: dict with total processed count and per-source results
    """
    output_dir = Path(config['output_dir'])

    # episode_indexing selects how season/episode numbers are written into
    # <episode-num> (see format_episode_num). "zero" (default) is the xmltv_ns
    # 0-based convention Emby expects; "one" keeps the raw 1-based numbers.
    # Fall back to "zero" on anything unexpected so we never emit garbage.
    indexing = config.get('episode_indexing', 'zero')
    if indexing not in ('zero', 'one'):
        print(f"Warning: invalid episode_indexing '{indexing}', defaulting to 'zero'")
        indexing = 'zero'

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    total_processed = 0
    results = {}

    for source in config['sources']:
        name = source['name']
        url = source['url']
        output_file = source['output']

        # Download to temporary file
        temp_file = f"{name}_raw.xml"
        print(f"Downloading {name} from {url}...")

        if not download_file(url, temp_file):
            results[name] = {'status': 'failed', 'error': 'download failed'}
            continue

        # Process the file
        output_path = output_dir / output_file
        print(f"Processing {name}...")

        try:
            count = process_epg(temp_file, str(output_path), indexing=indexing)
            total_processed += count
            results[name] = {'status': 'success', 'processed': count, 'output': str(output_path)}
            print(f"  -> {count} programmes processed, saved to {output_path}")
        except Exception as e:
            results[name] = {'status': 'failed', 'error': str(e)}
            print(f"  -> Error processing {name}: {e}")
        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)
    
    return {'total': total_processed, 'sources': results}


def main():
    parser = argparse.ArgumentParser(description='EPG Processor for Emby Live TV Plugin')
    parser.add_argument('--config', '-c', default='config.json',
                        help='Path to configuration file (default: config.json)')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    
    print(f"Processing {len(config['sources'])} source(s) from config: {args.config}")
    print(f"Output directory: {config['output_dir']}")
    
    # Process all sources
    results = process_all_sources(config)
    
    print(f"\nTotal programmes processed: {results['total']}")
    
    # Print summary
    print("\nResults:")
    for name, result in results['sources'].items():
        if result['status'] == 'success':
            print(f"  Success: {name}: {result['processed']} programmes -> {result['output']}")
        else:
            print(f"  Failed: {name}: {result.get('error', 'unknown error')}")
    
    all_failed = bool(results['sources']) and all(
        r['status'] == 'failed' for r in results['sources'].values()
    )
    print("\nDone!")
    if all_failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
