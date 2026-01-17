# Obsidian Vault Indexer

A Python script that creates a **privacy-safe map** of your Obsidian vault. Perfect for sharing your vault's structure with AI tools without exposing your actual notes or sensitive file names.

## What Problem Does This Solve?

You want to use AI assistants (ChatGPT, Claude, etc.) to help you organize or work with your Obsidian vault. But there's a catch:

- You don't want to share your actual notes (they're private!)
- You don't want to share your file names (they might contain personal info)
- But the AI needs to understand *how* your vault is organized

**This script creates a structural index** — a map that shows:
- Your folder hierarchy (folder names are visible)
- How many files are in each folder
- What naming patterns you use (like `YYYY-MM-DD.md` for daily notes)
- File types (markdown, images, PDFs, etc.)

**What it does NOT expose:**
- Your actual file names (they're redacted/hashed)
- Any content from your notes
- Links between notes
- Tags or metadata

## Quick Start

### 1. Download the Script

```bash
# Clone the repo
git clone https://github.com/id-guy/obsidian-vault-indexer.git
cd obsidian-vault-indexer

# Or just download vault_indexer.py directly
```

### 2. Run It

You have three options:

#### Option A: Interactive Mode (Easiest)
Just run the script and it will ask you questions:
```bash
python3 vault_indexer.py
```

#### Option B: Command Line Arguments
```bash
python3 vault_indexer.py --vault "/path/to/your/vault" --output "/path/to/output/index.md"
```

#### Option C: Config File (Best for Automation)
Create a `config.json` file:
```json
{
  "vault_path": "/path/to/your/obsidian/vault",
  "output_path": "/path/to/output/vault_index.md"
}
```

Then run:
```bash
python3 vault_indexer.py --config config.json
```

## Command Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--config` | `-c` | Path to a JSON config file |
| `--vault` | `-v` | Path to your Obsidian vault folder |
| `--output` | `-o` | Where to save the generated index |

**Note:** If using `--vault`, you must also provide `--output` (and vice versa).

## Example Output

Here's what the generated index looks like:

```markdown
# Obsidian Vault Index

**Vault**: `MyVault`
**Generated**: 2024-01-15T10:30:00

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Folders | 42 |
| Total Files | 500 |
| Max Depth | 4 levels |

### Naming Patterns Detected

| Pattern | Count | Format Example |
|---------|-------|----------------|
| daily_note | 365 | `YYYY-MM-DD.md` |
| standard | 135 | `[Any title].md` |

## Folder Structure

📁 MyVault/
├── 📁 Daily Notes/ (365 files)
├── 📁 Projects/ (50 files)
    ├── 📁 Work/
    ├── 📁 Personal/
├── 📁 Resources/
    ├── 📁 Books/ (20 files)
    ├── 📁 Articles/ (45 files)
```

Notice how file names are replaced with patterns like `[Note_a3f2c1] (~3 words in title).md` — this tells the AI "there's a note here with a 3-word title" without revealing what the title actually is.

## How Privacy Works

### What Gets Redacted

| Original Filename | What Appears in Index |
|-------------------|----------------------|
| `My therapy notes.md` | `[Note_7f2a91] (~3 words in title).md` |
| `2024-01-15.md` | `2024-01-15.md` (pattern shown, not real date) |
| `001 - Project Plan.md` | `001 - [Redacted Title].md` |

### The Hash Explained

When you see something like `[Note_7f2a91]`, that `7f2a91` is a **one-way hash** of the original filename. This means:
- The same filename always produces the same hash (consistency)
- You **cannot** reverse the hash to get the original filename (privacy)
- It's just 6 characters from an MD5 hash — short enough to be readable

### Folder Names Are Visible

By design, folder names are **not** redacted. This is because:
- Folder names are usually categories ("Projects", "Daily Notes") not sensitive content
- AI tools need folder context to understand your organization system

If your folder names contain sensitive info, you may want to rename them or modify the script.

## Automating with macOS (launchd)

Want this to run automatically? On macOS, you can use `launchd` (the system scheduler).

### 1. Create a plist file

Save this as `~/Library/LaunchAgents/com.user.vaultindexer.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.vaultindexer</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/vault_indexer.py</string>
        <string>--config</string>
        <string>/path/to/config.json</string>
    </array>

    <!-- Run every 4 hours (14400 seconds) -->
    <key>StartInterval</key>
    <integer>14400</integer>

    <!-- Also run when first loaded -->
    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/vaultindexer.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/vaultindexer.error.log</string>
</dict>
</plist>
```

### 2. Load it

```bash
launchctl load ~/Library/LaunchAgents/com.user.vaultindexer.plist
```

### 3. Useful Commands

```bash
# Check if it's running
launchctl list | grep vaultindexer

# Stop it
launchctl unload ~/Library/LaunchAgents/com.user.vaultindexer.plist

# View logs
cat /tmp/vaultindexer.log
cat /tmp/vaultindexer.error.log
```

## Detected Naming Patterns

The script automatically detects these common Obsidian naming conventions:

| Pattern | Example | Used For |
|---------|---------|----------|
| `daily_note` | `2024-01-15.md` | Daily notes |
| `weekly_note` | `2024-W03.md` | Weekly notes |
| `zettelkasten` | `20240115143022.md` | Zettelkasten timestamps |
| `numbered_prefix` | `001 - Note Title.md` | Numbered/ordered notes |
| `uuid` | `a1b2c3d4-e5f6-...` | UUID-based naming |
| `standard` | Any other title | Regular notes |

## Files Ignored

The script automatically skips:
- `.obsidian/` (Obsidian's config folder)
- `.trash/` (Obsidian's trash)
- `.git/` (git repositories)
- `.DS_Store` (macOS system files)
- `node_modules/` (if you have any plugins with dependencies)
- Any hidden files (starting with `.`)

## Requirements

- **Python 3.6+** (comes pre-installed on macOS)
- No external dependencies! Uses only Python standard library.

## Keeping Your Config Private

If you're pushing to your own fork or repo:

1. The included `.gitignore` already ignores `config.json`
2. Use `config.example.json` as a template
3. Copy it to `config.json` and add your real paths
4. Your `config.json` stays local and private

## Troubleshooting

### "Vault path not found"
- Make sure the path is correct
- On macOS, iCloud paths look like: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/YourVault`
- Use `ls` to verify the path exists

### "Permission denied"
- The script needs read access to your vault folder
- Check System Preferences > Security & Privacy > Files and Folders

### The output is empty or missing folders
- Hidden folders (starting with `.`) are intentionally skipped
- Check if your vault structure uses hidden folders

## Contributing

Found a bug? Have an idea? Feel free to open an issue or PR!

## License

MIT — do whatever you want with it.

---

Built with privacy in mind. Your notes are yours.
