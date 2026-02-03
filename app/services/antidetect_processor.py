"""
Anti-AI-Detection Post-Processing Service
Applies Q30 processing pipeline that achieved 87.2% on Hive detector
"""

from PIL import Image, ImageFilter
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Union
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AntiDetectProcessor:
    """
    Post-processor that applies anti-AI-detection treatments to images.
    Best result: Q30 compression with noise/degradation achieved 87.2% on Hive.
    """
    
    def __init__(self, quality: int = 30):
        self.quality = quality
        
    def process(
        self, 
        input_path: Union[str, Path, bytes],
        output_path: Optional[Union[str, Path]] = None,
        save_original: bool = True
    ) -> Path:
        """
        Apply anti-detection processing to an image.
        
        Args:
            input_path: Path to input image or raw bytes
            output_path: Optional output path. If None, generates automatically.
            save_original: If True, keeps original and creates new file
            
        Returns:
            Path to processed image
        """
        if isinstance(input_path, bytes):
            img = Image.open(io.BytesIO(input_path))
            input_path = Path("temp_input.png")
        else:
            input_path = Path(input_path)
            img = Image.open(input_path)
        
        original_size = img.size
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        for _ in range(3):
            small = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
            img = small.resize(original_size, Image.LANCZOS)
        
        img_array = np.array(img, dtype=np.float32)
        
        noise = np.random.normal(0, 25, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        for c in range(3):
            channel_noise = np.random.normal(0, 8, img_array[:,:,c].shape)
            img_array[:,:,c] = np.clip(img_array[:,:,c] + channel_noise, 0, 255)
        
        img_array = img_array * 0.92 + 10
        
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        img_processed = img_processed.filter(ImageFilter.GaussianBlur(radius=0.8))
        
        width, height = img_processed.size
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        vignette = 1 - 0.3 * (X**2 + Y**2)
        vignette = np.clip(vignette, 0, 1)
        vignette_3d = np.stack([vignette] * 3, axis=-1)
        img_array = np.array(img_processed, dtype=np.float32) * vignette_3d
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        grain = np.random.normal(0, 12, (height, width, 3))
        img_array = np.array(img_processed, dtype=np.float32) + grain
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        if img_processed.mode == 'RGBA':
            img_processed = img_processed.convert('RGB')
        
        if output_path is None:
            if isinstance(input_path, Path) and input_path.exists():
                stem = input_path.stem
                output_path = input_path.parent / f"{stem}_antidetect_q{self.quality}.jpg"
            else:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = Path(f"antidetect_{ts}_q{self.quality}.jpg")
        else:
            output_path = Path(output_path)
        
        if output_path.suffix.lower() != '.jpg':
            output_path = output_path.with_suffix('.jpg')
        
        img_processed.save(output_path, 'JPEG', quality=self.quality)
        
        logger.info(f"Anti-detect processed: {output_path} (Q{self.quality})")
        return output_path
    
    def process_bytes(self, image_bytes: bytes) -> bytes:
        """
        Process image bytes and return processed bytes.
        Useful for in-memory processing without file I/O.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Processed image as JPEG bytes
        """
        img = Image.open(io.BytesIO(image_bytes))
        original_size = img.size
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        for _ in range(3):
            small = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
            img = small.resize(original_size, Image.LANCZOS)
        
        img_array = np.array(img, dtype=np.float32)
        
        noise = np.random.normal(0, 25, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        for c in range(3):
            channel_noise = np.random.normal(0, 8, img_array[:,:,c].shape)
            img_array[:,:,c] = np.clip(img_array[:,:,c] + channel_noise, 0, 255)
        
        img_array = img_array * 0.92 + 10
        
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        img_processed = img_processed.filter(ImageFilter.GaussianBlur(radius=0.8))
        
        width, height = img_processed.size
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        vignette = 1 - 0.3 * (X**2 + Y**2)
        vignette = np.clip(vignette, 0, 1)
        vignette_3d = np.stack([vignette] * 3, axis=-1)
        img_array = np.array(img_processed, dtype=np.float32) * vignette_3d
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        grain = np.random.normal(0, 12, (height, width, 3))
        img_array = np.array(img_processed, dtype=np.float32) + grain
        img_processed = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        if img_processed.mode == 'RGBA':
            img_processed = img_processed.convert('RGB')
        
        buffer = io.BytesIO()
        img_processed.save(buffer, 'JPEG', quality=self.quality)
        return buffer.getvalue()


antidetect_processor = AntiDetectProcessor(quality=30)
