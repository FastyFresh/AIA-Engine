#!/usr/bin/env bash
#
# env.sh
# Source this script to set up temp directories and cache paths
# Usage: source scripts/env.sh
#

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

export TMPDIR="$PROJECT_ROOT/tmp"
export XDG_CACHE_HOME="$PROJECT_ROOT/cache"
export TRANSFORMERS_CACHE="$PROJECT_ROOT/cache/transformers"
export HF_HOME="$PROJECT_ROOT/cache/huggingface"
export TORCH_HOME="$PROJECT_ROOT/cache/torch"
export PIP_CACHE_DIR="$PROJECT_ROOT/cache/pip"

mkdir -p "$TMPDIR"
mkdir -p "$XDG_CACHE_HOME"
mkdir -p "$TRANSFORMERS_CACHE"
mkdir -p "$HF_HOME"
mkdir -p "$TORCH_HOME"
mkdir -p "$PIP_CACHE_DIR"

echo "Environment configured:"
echo "  TMPDIR=$TMPDIR"
echo "  XDG_CACHE_HOME=$XDG_CACHE_HOME"
echo "  TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE"
echo "  HF_HOME=$HF_HOME"
echo "  TORCH_HOME=$TORCH_HOME"
echo "  PIP_CACHE_DIR=$PIP_CACHE_DIR"
