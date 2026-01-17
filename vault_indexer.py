#!/usr/bin/env python3
"""
Obsidian Vault Indexer
Creates a privacy-safe structural index of an Obsidian vault.
Folder names are preserved, file names are redacted but patterns are detected.

Usage:
    python vault_indexer.py --config config.json
    python vault_indexer.py --vault /path/to/vault --output /path/to/output.md
    python vault_indexer.py  (interactive mode)
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, Tuple, Optional

# Folders/files to skip (Obsidian internals, etc.)
SKIP_PATTERNS = ['.obsidian', '.trash', '.git', '.DS_Store', 'node_modules']


def load_config(config_path: str) -> Dict:
    """Load configuration from a JSON file."""
    with open(config_path, 'r') as f:
        config = json.load(f)

    required = ['vault_path', 'output_path']
    for key in required:
        if key not in config:
            raise ValueError(f"Config file missing required key: {key}")

    return config


def interactive_setup() -> Tuple[str, str]:
    """Prompt user for paths interactively."""
    print("\n🔧 Vault Indexer Setup")
    print("=" * 40)
    print("\nChoose configuration method:\n")
    print("  1. Use a config file")
    print("  2. Enter paths manually\n")

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice in ('1', '2'):
            break
        print("Please enter 1 or 2")

    if choice == '1':
        config_path = input("\nEnter path to config file: ").strip()
        config_path = os.path.expanduser(config_path)

        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            print("\nCreate a config.json file with this structure:")
            print(json.dumps({
                "vault_path": "/path/to/your/obsidian/vault",
                "output_path": "/path/to/output/vault_index.md"
            }, indent=2))
            sys.exit(1)

        config = load_config(config_path)
        return config['vault_path'], config['output_path']

    else:
        print("\n📁 Enter your Obsidian vault path")
        print("   Example: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyVault")
        vault_path = input("\nVault path: ").strip()
        vault_path = os.path.expanduser(vault_path)

        print("\n📄 Enter output path for the index file")
        print("   Example: ~/Documents/vault_index.md")
        output_path = input("\nOutput path: ").strip()
        output_path = os.path.expanduser(output_path)

        # Offer to save as config
        print("\n💾 Save these paths to a config file for future use?")
        save = input("   Enter filename (or press Enter to skip): ").strip()

        if save:
            save_path = os.path.expanduser(save)
            if not save_path.endswith('.json'):
                save_path += '.json'

            config = {
                "vault_path": vault_path,
                "output_path": output_path
            }
            with open(save_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"   ✅ Config saved to: {save_path}")
            print(f"   Next time run: python vault_indexer.py --config {save_path}")

        return vault_path, output_path


def detect_filename_pattern(filename: str) -> Tuple[str, str]:
    """
    Detect naming patterns in filenames and return (pattern_type, example_format).
    """
    name = Path(filename).stem  # Remove extension

    # Daily note patterns
    if re.match(r'^\d{4}-\d{2}-\d{2}$', name):
        return ('daily_note', 'YYYY-MM-DD')
    if re.match(r'^\d{4}\.\d{2}\.\d{2}$', name):
        return ('daily_note', 'YYYY.MM.DD')
    if re.match(r'^\d{2}-\d{2}-\d{4}$', name):
        return ('daily_note', 'MM-DD-YYYY')

    # Weekly notes
    if re.match(r'^\d{4}-W\d{2}$', name, re.IGNORECASE):
        return ('weekly_note', 'YYYY-Www')

    # Timestamps
    if re.match(r'^\d{14}$', name):  # Zettelkasten-style
        return ('zettelkasten', 'YYYYMMDDHHmmss')
    if re.match(r'^\d{12}$', name):
        return ('timestamp', 'YYYYMMDDHHmm')

    # Prefixed notes (numbered)
    if re.match(r'^\d+[\s\-_\.]+', name):
        return ('numbered_prefix', 'NNN - [Title]')

    # UUID-style
    if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', name, re.IGNORECASE):
        return ('uuid', 'UUID')

    return ('standard', '[Title]')


def redact_filename(filename: str, pattern_type: str) -> str:
    """
    Create a redacted version of the filename that preserves pattern info.
    """
    ext = Path(filename).suffix
    name = Path(filename).stem

    if pattern_type == 'daily_note':
        # Show pattern with fake date
        if '-' in name:
            return f"2024-01-15{ext}"
        return f"2024.01.15{ext}"

    if pattern_type == 'weekly_note':
        return f"2024-W03{ext}"

    if pattern_type == 'zettelkasten':
        return f"20240115143022{ext}"

    if pattern_type == 'timestamp':
        return f"202401151430{ext}"

    if pattern_type == 'numbered_prefix':
        prefix_match = re.match(r'^(\d+[\s\-_\.]+)', name)
        if prefix_match:
            return f"{prefix_match.group(1)}[Redacted Title]{ext}"

    if pattern_type == 'uuid':
        return f"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx{ext}"

    # Standard: create a short hash-based placeholder
    short_hash = hashlib.md5(name.encode()).hexdigest()[:6]
    word_count = len(name.split())
    return f"[Note_{short_hash}] (~{word_count} words in title){ext}"


def get_file_type_category(filename: str) -> str:
    """Categorize files by extension."""
    ext = Path(filename).suffix.lower()

    categories = {
        'notes': ['.md', '.markdown', '.txt'],
        'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp'],
        'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
        'audio': ['.mp3', '.wav', '.m4a', '.ogg', '.flac'],
        'video': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
        'data': ['.json', '.csv', '.yaml', '.yml', '.xml'],
        'code': ['.py', '.js', '.ts', '.html', '.css', '.sh'],
        'canvas': ['.canvas'],
    }

    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return 'other'


def scan_vault(vault_path: str) -> Dict:
    """
    Scan the vault and build a structural representation.
    """
    vault = Path(vault_path)

    structure = {
        'root': vault.name,
        'scanned_at': datetime.now().isoformat(),
        'folders': {},
        'stats': {
            'total_folders': 0,
            'total_files': 0,
            'file_types': defaultdict(int),
            'patterns_found': defaultdict(int),
            'depth_max': 0,
        }
    }

    for root, dirs, files in os.walk(vault):
        # Filter out skipped directories
        dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS and not d.startswith('.')]

        rel_path = os.path.relpath(root, vault)
        if rel_path == '.':
            rel_path = ''

        depth = len(rel_path.split(os.sep)) if rel_path else 0
        structure['stats']['depth_max'] = max(structure['stats']['depth_max'], depth)

        # Filter files
        valid_files = [f for f in files if f not in SKIP_PATTERNS and not f.startswith('.')]

        if valid_files or dirs:
            folder_info = {
                'file_count': len(valid_files),
                'subfolder_count': len(dirs),
                'files': [],
                'depth': depth,
            }

            for filename in valid_files:
                pattern_type, pattern_format = detect_filename_pattern(filename)
                redacted = redact_filename(filename, pattern_type)
                file_type = get_file_type_category(filename)

                folder_info['files'].append({
                    'redacted_name': redacted,
                    'pattern': pattern_type,
                    'type': file_type,
                    'extension': Path(filename).suffix,
                })

                structure['stats']['file_types'][file_type] += 1
                structure['stats']['patterns_found'][pattern_type] += 1
                structure['stats']['total_files'] += 1

            structure['folders'][rel_path if rel_path else '/'] = folder_info
            if rel_path:
                structure['stats']['total_folders'] += 1

    return structure


def generate_tree(structure: Dict) -> str:
    """Generate an ASCII tree representation of the folder structure."""
    lines = [f"📁 {structure['root']}/"]

    # Sort folders by path for consistent tree
    sorted_folders = sorted(structure['folders'].items(), key=lambda x: x[0])

    # Build tree structure
    for folder_path, info in sorted_folders:
        if folder_path == '/':
            continue

        parts = folder_path.split(os.sep)
        indent = "    " * (len(parts) - 1) + "├── "

        file_summary = f"({info['file_count']} files)" if info['file_count'] > 0 else ""
        lines.append(f"{indent}📁 {parts[-1]}/ {file_summary}")

    return '\n'.join(lines)


def generate_markdown(structure: Dict) -> str:
    """Generate the final markdown index."""
    stats = structure['stats']

    md = f"""# Obsidian Vault Index

> **Privacy Note**: This index shows vault structure only. File names are redacted; actual note content is never accessed.

**Vault**: `{structure['root']}`
**Generated**: {structure['scanned_at']}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Folders | {stats['total_folders']} |
| Total Files | {stats['total_files']} |
| Max Depth | {stats['depth_max']} levels |

### Files by Type

| Type | Count |
|------|-------|
"""

    for file_type, count in sorted(stats['file_types'].items(), key=lambda x: -x[1]):
        md += f"| {file_type} | {count} |\n"

    md += """
### Naming Patterns Detected

| Pattern | Count | Format Example |
|---------|-------|----------------|
"""

    pattern_examples = {
        'daily_note': 'YYYY-MM-DD.md',
        'weekly_note': 'YYYY-Www.md',
        'zettelkasten': 'YYYYMMDDHHmmss.md',
        'timestamp': 'YYYYMMDDHHmm.md',
        'numbered_prefix': '001 - Title.md',
        'uuid': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.md',
        'standard': '[Any title].md',
    }

    for pattern, count in sorted(stats['patterns_found'].items(), key=lambda x: -x[1]):
        example = pattern_examples.get(pattern, '[Unknown]')
        md += f"| {pattern} | {count} | `{example}` |\n"

    md += f"""
---

## Folder Structure

```
{generate_tree(structure)}
```

---

## Detailed Folder Contents

"""

    for folder_path, info in sorted(structure['folders'].items()):
        display_path = folder_path if folder_path != '/' else '(root)'
        md += f"### 📁 `{display_path}`\n\n"

        if info['files']:
            md += "| Redacted Name | Pattern | Type |\n"
            md += "|---------------|---------|------|\n"

            # Show up to 5 examples per folder, grouped by pattern
            shown = 0
            seen_patterns = set()
            for file_info in info['files']:
                pattern = file_info['pattern']
                if pattern not in seen_patterns or shown < 3:
                    md += f"| `{file_info['redacted_name']}` | {pattern} | {file_info['type']} |\n"
                    seen_patterns.add(pattern)
                    shown += 1
                if shown >= 5:
                    break

            remaining = len(info['files']) - shown
            if remaining > 0:
                md += f"\n*...and {remaining} more files*\n"
        else:
            md += "*Empty folder or contains only subfolders*\n"

        md += "\n"

    md += """---

## How to Use This Index

This index is designed for AI assistants to understand your vault's organization without accessing private content.

**What's included:**
- Complete folder hierarchy with real folder names
- File counts and types per folder
- Detected naming patterns (e.g., daily notes format)
- Redacted file names showing structure only

**What's NOT included:**
- Actual file names or titles
- File contents
- Links between notes
- Tags or metadata

**For AI tools**: Use this to understand where different types of notes live, how the user organizes their vault, and what naming conventions they use.
"""

    return md


def main():
    parser = argparse.ArgumentParser(
        description='Create a privacy-safe index of an Obsidian vault.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.json
  %(prog)s --vault ~/MyVault --output ~/vault_index.md
  %(prog)s  (interactive mode)
        """
    )

    parser.add_argument(
        '--config', '-c',
        help='Path to JSON config file containing vault_path and output_path'
    )
    parser.add_argument(
        '--vault', '-v',
        help='Path to Obsidian vault directory'
    )
    parser.add_argument(
        '--output', '-o',
        help='Path for output markdown file'
    )

    args = parser.parse_args()

    # Determine paths based on arguments
    if args.config:
        # Config file mode
        config_path = os.path.expanduser(args.config)
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return 1

        config = load_config(config_path)
        vault_path = os.path.expanduser(config['vault_path'])
        output_path = os.path.expanduser(config['output_path'])

    elif args.vault and args.output:
        # Command-line arguments mode
        vault_path = os.path.expanduser(args.vault)
        output_path = os.path.expanduser(args.output)

    elif args.vault or args.output:
        # Partial arguments - error
        print("❌ Error: Both --vault and --output are required when not using --config")
        parser.print_help()
        return 1

    else:
        # Interactive mode
        vault_path, output_path = interactive_setup()

    # Run the indexer
    print(f"\n🔍 Scanning vault: {vault_path}")

    if not os.path.exists(vault_path):
        print(f"❌ Error: Vault path not found: {vault_path}")
        return 1

    structure = scan_vault(vault_path)

    print(f"📊 Found {structure['stats']['total_folders']} folders, {structure['stats']['total_files']} files")

    markdown = generate_markdown(structure)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✅ Index saved to: {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
