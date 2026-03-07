"""
Transform Bridge — Adds --transform flag support to nsfw_pipeline.py
Import this and call integrate() to add transform capability to the existing pipeline.

Usage from nsfw_pipeline.py:
    from transform_bridge import add_transform_args, handle_transform

    # In argument parser setup:
    add_transform_args(parser)

    # Before normal pipeline execution:
    if handle_transform(args):
        sys.exit(0)  # Transform handled it
"""

import argparse
import sys
from typing import Optional


def add_transform_args(parser: argparse.ArgumentParser):
    """Add transform-mode arguments to an existing argparse parser."""
    transform_group = parser.add_argument_group("Transform Mode")
    transform_group.add_argument(
        "--transform", action="store_true",
        help="Transform mode: use input image as base, apply LoRA identity on top"
    )
    transform_group.add_argument(
        "--transform-input", "-ti",
        help="Input image path for transform mode"
    )
    transform_group.add_argument(
        "--transform-dir", "-td",
        help="Input directory for batch transform mode"
    )
    transform_group.add_argument(
        "--transform-strength", "-ts", type=float,
        help="img2img strength for transform (0.0-1.0, default: 0.62)"
    )
    transform_group.add_argument(
        "--transform-preset", "-tp",
        choices=["light", "balanced", "strong", "full"],
        help="Strength preset for transform"
    )
    transform_group.add_argument(
        "--transform-character", "-tc",
        default="starbright_monroe",
        help="Character for transform (default: starbright_monroe)"
    )


def handle_transform(args) -> bool:
    """
    Check if transform mode was requested and execute it.
    Returns True if transform was handled, False if normal pipeline should continue.
    """
    if not getattr(args, "transform", False):
        return False

    # Import here to avoid circular deps
    from transform_mode import transform_image, batch_transform, STRENGTH_PRESETS

    kwargs = {
        "character": getattr(args, "transform_character", "starbright_monroe"),
    }

    # Apply preset
    preset_name = getattr(args, "transform_preset", None)
    if preset_name:
        preset = STRENGTH_PRESETS[preset_name]
        kwargs["strength"] = preset["strength"]
        kwargs["lora_scale"] = preset["lora_scale"]

    # Override with explicit strength
    strength = getattr(args, "transform_strength", None)
    if strength is not None:
        kwargs["strength"] = strength

    # Single image
    input_path = getattr(args, "transform_input", None)
    if input_path:
        result = transform_image(input_path=input_path, **kwargs)
        if result["success"]:
            print(f"✓ Transform: {result['output_path']}")
        else:
            print(f"✗ Transform failed: {result.get('error')}")
        return True

    # Batch
    input_dir = getattr(args, "transform_dir", None)
    if input_dir:
        results = batch_transform(input_dir=input_dir, **kwargs)
        passed = sum(1 for r in results if r.get("success"))
        print(f"Batch: {passed}/{len(results)} succeeded")
        return True

    print("Error: --transform requires --transform-input or --transform-dir")
    return True
