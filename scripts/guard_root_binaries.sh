#!/usr/bin/env bash
#
# guard_root_binaries.sh
# Scans project root for large binary files and optionally moves them to artifacts/
#

set -euo pipefail

SIZE_THRESHOLD_MB="${SIZE_THRESHOLD_MB:-50}"
ARTIFACTS_DIR="artifacts"
MOVE_MODE=false
FOUND_LARGE=false

usage() {
    echo "Usage: $0 [--move] [--size SIZE_MB]"
    echo ""
    echo "Scans the project root for files larger than SIZE_MB (default: 50MB)"
    echo ""
    echo "Options:"
    echo "  --move       Auto-move large files to $ARTIFACTS_DIR/ with timestamp"
    echo "  --size N     Set size threshold to N megabytes (default: 50)"
    echo "  -h, --help   Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --move)
            MOVE_MODE=true
            shift
            ;;
        --size)
            if [[ -z "${2:-}" ]] || [[ ! "$2" =~ ^[0-9]+$ ]]; then
                echo "Error: --size requires a numeric argument"
                usage
            fi
            SIZE_THRESHOLD_MB="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

echo "========================================"
echo "Root Binary Guard"
echo "========================================"
echo "Threshold: ${SIZE_THRESHOLD_MB}MB"
echo "Mode: $(if $MOVE_MODE; then echo 'Move to artifacts/'; else echo 'Report only'; fi)"
echo ""

mkdir -p "$ARTIFACTS_DIR"

LARGE_FILES=$(find . -maxdepth 1 -type f -size "+${SIZE_THRESHOLD_MB}M" 2>/dev/null || true)

if [[ -z "$LARGE_FILES" ]]; then
    echo "No files larger than ${SIZE_THRESHOLD_MB}MB found in project root."
    echo "All clear!"
    exit 0
fi

echo "WARNING: Found large files in project root:"
echo ""

while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        FOUND_LARGE=true
        SIZE=$(du -h "$file" | cut -f1)
        FILENAME=$(basename "$file")
        echo "  [$SIZE] $FILENAME"
        
        if $MOVE_MODE; then
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            NEW_NAME="${TIMESTAMP}_${FILENAME}"
            mv "$file" "$ARTIFACTS_DIR/$NEW_NAME"
            echo "    -> Moved to $ARTIFACTS_DIR/$NEW_NAME"
        fi
    fi
done <<< "$LARGE_FILES"

echo ""

if $FOUND_LARGE && ! $MOVE_MODE; then
    echo "Run with --move to auto-relocate these files to $ARTIFACTS_DIR/"
    exit 1
fi

if $MOVE_MODE; then
    echo "All large files have been moved to $ARTIFACTS_DIR/"
fi

exit 0
