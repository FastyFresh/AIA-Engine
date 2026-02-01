from pathlib import Path

IMAGE_GLOBS = ("*.webp", "*.png", "*.jpg", "*.jpeg")

def list_images(folder: Path) -> list[Path]:
    files: list[Path] = []
    for g in IMAGE_GLOBS:
        files.extend(folder.glob(g))
    return files

def count_images(folder: Path) -> int:
    return sum(1 for g in IMAGE_GLOBS for _ in folder.glob(g))
