# Project

## Project Size & Artifact Policy

### Directory Structure

```
project/
├── tmp/           # Temporary files (auto-cleaned)
├── outputs/       # Generated images/videos/results
├── artifacts/     # Models, weights, large binaries
├── cache/         # Downloads, caches for AI tools
├── logs/          # Runtime logs
├── content/       # Media content (protected)
└── scripts/       # Utility scripts
```

### Rules

1. **Root directory should contain code only** - No large binaries, media files, or generated content in the project root
2. **All binaries/media go in outputs/ or artifacts/** - Generated content goes to `outputs/`, model weights and binaries go to `artifacts/`
3. **Cache paths are redirected** - ML tooling caches are directed to `cache/` subdirectory

### Scripts

#### Guard Script - Detect Large Files in Root

Scans the project root for files larger than 50MB (configurable):

```bash
# Check for large files (report only)
bash scripts/guard_root_binaries.sh

# Auto-move large files to artifacts/
bash scripts/guard_root_binaries.sh --move

# Custom size threshold (e.g., 100MB)
bash scripts/guard_root_binaries.sh --size 100
```

#### Environment Setup - Redirect Cache Paths

Sets up environment variables to redirect temp files and ML caches:

```bash
# Source before running the app
source scripts/env.sh
```

This configures:
- `TMPDIR` → `./tmp`
- `XDG_CACHE_HOME` → `./cache`
- `TRANSFORMERS_CACHE` → `./cache/transformers`
- `HF_HOME` → `./cache/huggingface`
- `TORCH_HOME` → `./cache/torch`
- `PIP_CACHE_DIR` → `./cache/pip`

#### Cleanup Utility - Free Up Space

Safely removes cache directories:

```bash
# Remove safe caches (.cache/pip, .cache/huggingface, etc.)
bash scripts/cleanup_caches.sh

# Also remove node_modules
bash scripts/cleanup_caches.sh --node

# Also remove .pythonlibs
bash scripts/cleanup_caches.sh --python

# Skip confirmation
bash scripts/cleanup_caches.sh --yes
```

#### Media Deduplication

Scans for duplicate media files and merges unique ones:

```bash
python scripts/deduplicate_media.py
```

### Pre-Run Checklist

1. Run `bash scripts/guard_root_binaries.sh` to check for oversized files
2. Run `source scripts/env.sh` to set up cache paths
3. Start the application

### Troubleshooting Space Issues

Check what's using space:
```bash
du -h --max-depth=2 | sort -hr | head -10
```

Clean up safely:
```bash
bash scripts/cleanup_caches.sh --yes
```
