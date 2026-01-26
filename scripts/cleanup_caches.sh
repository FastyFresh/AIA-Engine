#!/usr/bin/env bash
#
# cleanup_caches.sh
# Safely delete cache directories with confirmation
#

set -euo pipefail

REMOVE_NODE=false
REMOVE_PYTHON=false
AUTO_YES=false

SAFE_DIRS=(
)

CACHE_SUBDIRS_TO_CLEAN=(
    "./.cache/pip"
    "./.cache/huggingface"
    "./.cache/torch"
    "./.cache/transformers"
)

usage() {
    echo "Usage: $0 [--node] [--python] [--yes]"
    echo ""
    echo "Safely remove cache directories to free up space."
    echo ""
    echo "By default, removes only safe caches:"
    echo "  - .cache/pip, .cache/huggingface, .cache/torch, .cache/transformers"
    echo "  (Note: .cache/replit and .local/state/replit are protected by Replit)"
    echo ""
    echo "Options:"
    echo "  --node     Also remove node_modules/"
    echo "  --python   Also remove .pythonlibs/"
    echo "  --yes      Skip confirmation prompt"
    echo "  -h, --help Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --node)
            REMOVE_NODE=true
            shift
            ;;
        --python)
            REMOVE_PYTHON=true
            shift
            ;;
        --yes)
            AUTO_YES=true
            shift
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
echo "Cache Cleanup Utility"
echo "========================================"
echo ""

DIRS_TO_REMOVE=()

for dir in "${SAFE_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        DIRS_TO_REMOVE+=("$dir")
    fi
done

for dir in "${CACHE_SUBDIRS_TO_CLEAN[@]}"; do
    if [[ -d "$dir" ]]; then
        DIRS_TO_REMOVE+=("$dir")
    fi
done

if $REMOVE_NODE && [[ -d "./node_modules" ]]; then
    DIRS_TO_REMOVE+=("./node_modules")
fi

if $REMOVE_PYTHON && [[ -d "./.pythonlibs" ]]; then
    DIRS_TO_REMOVE+=("./.pythonlibs")
fi

if [[ ${#DIRS_TO_REMOVE[@]} -eq 0 ]]; then
    echo "No cache directories found to remove."
    exit 0
fi

echo "BEFORE cleanup:"
TOTAL_BEFORE=$(du -sh . 2>/dev/null | cut -f1)
echo "  Total project size: $TOTAL_BEFORE"
echo ""

echo "The following directories will be removed:"
for dir in "${DIRS_TO_REMOVE[@]}"; do
    SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "?")
    echo "  [$SIZE] $dir"
done
echo ""

if ! $AUTO_YES; then
    read -rp "Proceed with deletion? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ""
echo "Removing directories..."
for dir in "${DIRS_TO_REMOVE[@]}"; do
    echo "  Removing $dir..."
    rm -rf "$dir"
done

echo ""
echo "AFTER cleanup:"
TOTAL_AFTER=$(du -sh . 2>/dev/null | cut -f1)
echo "  Total project size: $TOTAL_AFTER"
echo ""
echo "Cleanup complete!"
echo "  Before: $TOTAL_BEFORE"
echo "  After:  $TOTAL_AFTER"
