#!/usr/bin/env python3
"""
Media Deduplication Agent
Scans directories for media files, identifies duplicates by content hash,
and consolidates unique files into a single merged directory.
"""

import os
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime

# Supported media extensions
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
    '.mp4', '.mov', '.avi', '.mkv', '.webm',
    '.pdf'
}

def calculate_file_hash(filepath, chunk_size=8192):
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (IOError, OSError) as e:
        print(f"  Error reading {filepath}: {e}")
        return None

def is_media_file(filepath):
    """Check if file is a supported media type."""
    return Path(filepath).suffix.lower() in MEDIA_EXTENSIONS

def scan_directory(base_path, exclude_dirs=None):
    """Scan directory for media files."""
    exclude_dirs = exclude_dirs or {'.git', 'node_modules', '.pythonlibs', '__pycache__', '.cache'}
    media_files = []
    
    for root, dirs, files in os.walk(base_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            if is_media_file(filepath):
                media_files.append(filepath)
    
    return media_files

def find_duplicates(media_files):
    """Find duplicate files by hash."""
    hash_to_files = defaultdict(list)
    
    print(f"\nScanning {len(media_files)} media files for duplicates...")
    
    for i, filepath in enumerate(media_files, 1):
        if i % 20 == 0:
            print(f"  Processed {i}/{len(media_files)} files...")
        
        file_hash = calculate_file_hash(filepath)
        if file_hash:
            hash_to_files[file_hash].append(filepath)
    
    # Separate unique and duplicate files
    unique_files = {}
    duplicates = {}
    
    for file_hash, files in hash_to_files.items():
        # Keep the file with shortest path or first alphabetically as the "original"
        files_sorted = sorted(files, key=lambda x: (len(x), x))
        unique_files[file_hash] = files_sorted[0]
        if len(files) > 1:
            duplicates[file_hash] = files_sorted[1:]
    
    return unique_files, duplicates

def get_unique_filename(dest_dir, original_name):
    """Generate a unique filename if conflict exists."""
    dest_path = os.path.join(dest_dir, original_name)
    if not os.path.exists(dest_path):
        return original_name
    
    name, ext = os.path.splitext(original_name)
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = os.path.join(dest_dir, new_name)
        if not os.path.exists(new_path):
            return new_name
        counter += 1

def merge_to_directory(unique_files, output_dir, organize_by_type=True):
    """Copy unique files to output directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    if organize_by_type:
        # Create subdirectories for organization
        subdirs = {
            'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff'},
            'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'},
            'video': {'.mp4', '.mov', '.avi', '.mkv', '.webm'},
            'documents': {'.pdf'}
        }
        for subdir in subdirs:
            os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    copied_files = []
    
    print(f"\nMerging {len(unique_files)} unique files to {output_dir}...")
    
    for file_hash, source_path in unique_files.items():
        ext = Path(source_path).suffix.lower()
        original_name = os.path.basename(source_path)
        
        # Determine destination subdirectory
        if organize_by_type:
            for subdir, extensions in subdirs.items():
                if ext in extensions:
                    dest_subdir = os.path.join(output_dir, subdir)
                    break
            else:
                dest_subdir = output_dir
        else:
            dest_subdir = output_dir
        
        # Get unique filename and copy
        unique_name = get_unique_filename(dest_subdir, original_name)
        dest_path = os.path.join(dest_subdir, unique_name)
        
        try:
            shutil.copy2(source_path, dest_path)
            copied_files.append({
                'source': source_path,
                'destination': dest_path,
                'hash': file_hash
            })
        except (IOError, OSError) as e:
            print(f"  Error copying {source_path}: {e}")
    
    return copied_files

def generate_report(media_files, unique_files, duplicates, copied_files, output_dir):
    """Generate a deduplication report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files_scanned': len(media_files),
            'unique_files': len(unique_files),
            'duplicate_files': sum(len(dups) for dups in duplicates.values()),
            'duplicate_groups': len(duplicates),
            'files_merged': len(copied_files),
            'output_directory': output_dir
        },
        'duplicates': {}
    }
    
    # Add duplicate details
    for file_hash, dup_files in duplicates.items():
        original = unique_files[file_hash]
        report['duplicates'][file_hash[:8]] = {
            'kept': original,
            'duplicates': dup_files
        }
    
    return report

def print_report(report):
    """Print human-readable report."""
    summary = report['summary']
    
    print("\n" + "="*60)
    print("MEDIA DEDUPLICATION REPORT")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"\nSUMMARY:")
    print(f"  Total files scanned:  {summary['total_files_scanned']}")
    print(f"  Unique files found:   {summary['unique_files']}")
    print(f"  Duplicate files:      {summary['duplicate_files']}")
    print(f"  Duplicate groups:     {summary['duplicate_groups']}")
    print(f"  Files merged:         {summary['files_merged']}")
    print(f"  Output directory:     {summary['output_directory']}")
    
    if report['duplicates']:
        print(f"\nDUPLICATES FOUND ({len(report['duplicates'])} groups):")
        for hash_prefix, info in list(report['duplicates'].items())[:10]:
            print(f"\n  [{hash_prefix}...]")
            print(f"    Kept: {info['kept']}")
            for dup in info['duplicates']:
                print(f"    Duplicate: {dup}")
        
        if len(report['duplicates']) > 10:
            print(f"\n  ... and {len(report['duplicates']) - 10} more duplicate groups")
    else:
        print("\nNo duplicates found!")
    
    print("\n" + "="*60)

def main():
    """Main deduplication workflow."""
    # Configuration
    scan_paths = ['./content']  # Directories to scan
    output_dir = './content/merged_media'
    report_file = './content/dedup_report.json'
    
    print("="*60)
    print("MEDIA DEDUPLICATION AGENT")
    print("="*60)
    
    # Step 1: Scan for media files
    print("\nStep 1: Scanning for media files...")
    all_media_files = []
    for scan_path in scan_paths:
        if os.path.exists(scan_path):
            files = scan_directory(scan_path)
            print(f"  Found {len(files)} media files in {scan_path}")
            all_media_files.extend(files)
        else:
            print(f"  Warning: {scan_path} does not exist")
    
    if not all_media_files:
        print("\nNo media files found. Exiting.")
        return
    
    # Step 2: Find duplicates
    print("\nStep 2: Finding duplicates by content hash...")
    unique_files, duplicates = find_duplicates(all_media_files)
    
    # Step 3: Merge unique files
    print("\nStep 3: Merging unique files...")
    copied_files = merge_to_directory(unique_files, output_dir, organize_by_type=True)
    
    # Step 4: Generate and save report
    print("\nStep 4: Generating report...")
    report = generate_report(all_media_files, unique_files, duplicates, copied_files, output_dir)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved to {report_file}")
    
    # Print summary
    print_report(report)
    
    print(f"\nDeduplication complete! Unique media files are now in: {output_dir}")

if __name__ == '__main__':
    main()
