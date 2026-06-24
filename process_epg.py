#!/usr/bin/env python3
"""EPG Processor for Emby Live TV Plugin

Extracts episode numbers from StarHub TV EPG and adds XMLTV metadata.
Supports multiple sources via config file.

Usage:
    python process_epg.py [--config CONFIG_FILE]

Configuration:
    See config.json for source definitions and output directory.
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


def format_episode_num(season, episode):
    """Format episode number for xmltv_ns system."""
    if season:
        return f"{season}.{int(episode):02d}"
    return episode


def process_epg(input_path, output_path):
    """Process EPG XML file to add episode-num elements."""
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

    # Write output with proper XML declaration
    tree.write(output_path, encoding='UTF-8', xml_declaration=True)
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
    
    return config


def process_all_sources(config):
    """
    Process all sources defined in config.
    
    Returns: dict with total processed count and per-source results
    """
    output_dir = Path(config['output_dir'])
    
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
            count = process_epg(temp_file, str(output_path))
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
    
    print("\nDone!")


if __name__ == '__main__':
    main()
