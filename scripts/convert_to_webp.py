#!/usr/bin/env python3
"""
WebP Conversion Script
Converts PNG/JPG images to WebP format with quality=88, method=6
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

def convert_folder(folder_path: Path, drop_alpha: bool = True) -> dict:
    """Convert all PNG/JPG/JPEG images in folder to WebP."""
    if not folder_path.exists():
        print(f"ERROR: Folder not found: {folder_path}")
        return {"converted": 0, "skipped": 0, "errors": [], "alpha_skipped": []}
    
    tmp_dir = folder_path.parent / f"{folder_path.name}_webp_tmp"
    tmp_dir.mkdir(exist_ok=True)
    
    stats = {"converted": 0, "skipped": 0, "errors": [], "alpha_skipped": []}
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG")
    
    all_files = []
    for ext in extensions:
        all_files.extend(folder_path.glob(ext))
    
    for img_path in all_files:
        out_path = tmp_dir / f"{img_path.stem}.webp"
        
        if out_path.exists():
            stats["skipped"] += 1
            continue
        
        try:
            with Image.open(img_path) as img:
                has_alpha = img.mode in ("RGBA", "LA", "PA") or (
                    img.mode == "P" and "transparency" in img.info
                )
                
                if has_alpha and not drop_alpha:
                    stats["alpha_skipped"].append(str(img_path))
                    stats["skipped"] += 1
                    continue
                
                if has_alpha and drop_alpha:
                    img = img.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                
                img.save(out_path, "WEBP", quality=88, method=6)
                stats["converted"] += 1
                
        except Exception as e:
            stats["errors"].append(f"{img_path}: {e}")
    
    print(f"Converted: {stats['converted']}, Skipped: {stats['skipped']}, Errors: {len(stats['errors'])}")
    if stats["alpha_skipped"]:
        print(f"Alpha skipped: {stats['alpha_skipped']}")
    if stats["errors"]:
        for err in stats["errors"]:
            print(f"  ERROR: {err}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Convert images to WebP")
    parser.add_argument("folder", type=Path, help="Folder containing images")
    parser.add_argument("--drop-alpha", action="store_true", default=True,
                        help="Drop alpha channel (default: True)")
    parser.add_argument("--keep-alpha", action="store_true",
                        help="Skip images with alpha instead of converting")
    args = parser.parse_args()
    
    drop_alpha = not args.keep_alpha
    stats = convert_folder(args.folder, drop_alpha=drop_alpha)
    return 0 if not stats["errors"] else 1

if __name__ == "__main__":
    sys.exit(main())
