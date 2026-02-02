"""
Automated Avatar Generation & Realism Enhancement Pipeline
Generates AI avatars and post-processes to reduce AI detection flags
"""

import os
import base64
import httpx
import replicate
import fal_client
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvatarRealismPipeline:
    """Pipeline to generate avatars and enhance realism to reduce AI detection"""
    
    def __init__(
        self,
        face_ref_path: str = "content/references/starbright_monroe/starbright_face_reference_v3.webp",
        body_ref_path: str = "content/references/starbright_monroe/body_reference_canonical.webp",
        output_dir: str = "content/pipeline_output"
    ):
        self.face_ref_path = face_ref_path
        self.body_ref_path = body_ref_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.face_uri = self._encode_image(face_ref_path)
        self.body_uri = self._encode_image(body_ref_path)
    
    def _encode_image(self, path: str) -> str:
        """Encode image to base64 data URI"""
        with open(path, 'rb') as f:
            data = f.read()
        ext = path.split('.')[-1].lower()
        mime = {
            'webp': 'image/webp',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg'
        }.get(ext, 'image/png')
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    
    def _save_image(self, url_or_bytes: any, prefix: str) -> Path:
        """Download and save image from URL or bytes"""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.output_dir / f"{prefix}_{ts}.png"
        
        if isinstance(url_or_bytes, bytes):
            filepath.write_bytes(url_or_bytes)
        else:
            url = url_or_bytes.url if hasattr(url_or_bytes, 'url') else str(url_or_bytes)
            resp = httpx.get(url, timeout=120.0)
            filepath.write_bytes(resp.content)
        
        logger.info(f"Saved: {filepath}")
        return filepath
    
    def step1_generate_avatar(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        guidance_scale: float = 3.5,
        num_inference_steps: int = 30
    ) -> Path:
        """
        Step 1: Initial avatar generation with Seedream 4.5
        Uses face and body references to create consistent identity
        """
        logger.info("Step 1: Generating initial avatar with Seedream 4.5...")
        
        full_prompt = f"""{prompt}
Very long straight sleek dark brown hair,
very pale porcelain ivory white skin with natural freckles across nose and cheeks,
warm olive-brown eyes, extremely thin slender petite body with very narrow tiny waist,
slim narrow hips, long thin slender legs,
photorealistic skin texture with visible pores and natural imperfections,
realistic fabric with natural wrinkles and folds,
soft natural lighting, sharp focus"""
        
        negative_prompt = """Smooth skin, airbrushed, plastic skin, perfect symmetry,
AI artifacts, over-smoothed, idealized fabric, stiff clothing, flat lighting,
blurry, low quality, distorted features"""
        
        output = replicate.run(
            'bytedance/seedream-4.5',
            input={
                'prompt': full_prompt,
                'negative_prompt': negative_prompt,
                'aspect_ratio': aspect_ratio,
                'output_format': 'png',
                'guidance_scale': guidance_scale,
                'num_inference_steps': num_inference_steps,
                'num_outputs': 1,
                'image_input': [self.face_uri, self.body_uri],
            }
        )
        
        if output:
            return self._save_image(output[0], "step1_avatar")
        raise Exception("Failed to generate initial avatar")
    
    def step2_enhance_skin_texture(self, image_path: Path) -> Path:
        """
        Step 2: Post-process skin to add realistic texture
        Adds pores, tonal variations, and subtle imperfections
        """
        logger.info("Step 2: Enhancing skin texture with Flux Kontext...")
        
        image_uri = self._encode_image(str(image_path))
        
        prompt = """Add realistic skin texture: visible pores on face especially nose and cheeks,
natural tonal variations and subtle redness on cheeks and nose tip,
tiny imperfections like barely visible freckles and skin texture,
natural skin shine on forehead and nose bridge,
keep all other elements exactly the same"""
        
        try:
            output = replicate.run(
                'black-forest-labs/flux-kontext-pro',
                input={
                    'prompt': prompt,
                    'input_image': image_uri,
                    'aspect_ratio': 'match_input_image',
                    'output_format': 'png',
                    'safety_tolerance': 6,
                }
            )
            
            if output:
                return self._save_image(output, "step2_skin")
        except Exception as e:
            logger.warning(f"Flux Kontext failed: {e}, trying fal.ai...")
        
        try:
            image_url = fal_client.upload_file(str(image_path))
            result = fal_client.subscribe(
                "fal-ai/flux/dev/image-to-image",
                arguments={
                    "image_url": image_url,
                    "prompt": prompt,
                    "strength": 0.35,
                    "num_inference_steps": 28,
                }
            )
            if result and 'images' in result:
                return self._save_image(result['images'][0]['url'], "step2_skin")
        except Exception as e:
            logger.warning(f"fal.ai fallback failed: {e}")
        
        logger.info("Skin enhancement skipped, using previous step")
        return image_path
    
    def step3_enhance_fabric_texture(self, image_path: Path) -> Path:
        """
        Step 3: Post-process fabric to add realistic wrinkles and folds
        Adds natural drape, creases, and fabric imperfections
        """
        logger.info("Step 3: Enhancing fabric texture...")
        
        image_uri = self._encode_image(str(image_path))
        
        prompt = """Add realistic fabric details: natural wrinkles and folds where fabric bends,
subtle creases from body movement, gravity-affected drape,
slight fabric texture variations and weave pattern visibility,
keep face and skin exactly the same, only enhance clothing realism"""
        
        try:
            output = replicate.run(
                'black-forest-labs/flux-kontext-pro',
                input={
                    'prompt': prompt,
                    'input_image': image_uri,
                    'aspect_ratio': 'match_input_image',
                    'output_format': 'png',
                    'safety_tolerance': 6,
                }
            )
            
            if output:
                return self._save_image(output, "step3_fabric")
        except Exception as e:
            logger.warning(f"Flux Kontext failed: {e}, trying fal.ai...")
        
        try:
            image_url = fal_client.upload_file(str(image_path))
            result = fal_client.subscribe(
                "fal-ai/flux/dev/image-to-image",
                arguments={
                    "image_url": image_url,
                    "prompt": prompt,
                    "strength": 0.3,
                    "num_inference_steps": 28,
                }
            )
            if result and 'images' in result:
                return self._save_image(result['images'][0]['url'], "step3_fabric")
        except Exception as e:
            logger.warning(f"fal.ai fallback failed: {e}")
        
        logger.info("Fabric enhancement skipped, using previous step")
        return image_path
    
    def step4_add_noise_and_upscale(
        self,
        image_path: Path,
        add_grain: bool = True,
        upscale: bool = False
    ) -> Path:
        """
        Step 4: Optional final refinement
        Adds subtle noise/grain and optionally upscales
        """
        logger.info("Step 4: Adding final touches (noise/grain)...")
        
        if not add_grain and not upscale:
            return image_path
        
        image_uri = self._encode_image(str(image_path))
        
        prompt = """Add very subtle film grain and natural image noise,
slight color grading for authentic photography look,
maintain all details exactly, just add subtle analog camera characteristics"""
        
        try:
            output = replicate.run(
                'black-forest-labs/flux-kontext-pro',
                input={
                    'prompt': prompt,
                    'input_image': image_uri,
                    'aspect_ratio': 'match_input_image',
                    'output_format': 'png',
                    'safety_tolerance': 6,
                }
            )
            
            if output:
                return self._save_image(output, "step4_final")
        except Exception as e:
            logger.warning(f"Final refinement failed: {e}")
        
        return image_path
    
    def run_full_pipeline(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        skip_skin: bool = False,
        skip_fabric: bool = False,
        skip_grain: bool = False
    ) -> Tuple[Path, dict]:
        """
        Run the complete avatar generation and realism enhancement pipeline
        
        Returns: (final_image_path, intermediate_paths_dict)
        """
        logger.info("=" * 60)
        logger.info("Starting Avatar Realism Pipeline")
        logger.info("=" * 60)
        
        intermediates = {}
        
        step1_result = self.step1_generate_avatar(prompt, aspect_ratio)
        intermediates['step1_initial'] = step1_result
        current = step1_result
        
        if not skip_skin:
            step2_result = self.step2_enhance_skin_texture(current)
            intermediates['step2_skin'] = step2_result
            current = step2_result
        
        if not skip_fabric:
            step3_result = self.step3_enhance_fabric_texture(current)
            intermediates['step3_fabric'] = step3_result
            current = step3_result
        
        if not skip_grain:
            step4_result = self.step4_add_noise_and_upscale(current)
            intermediates['step4_final'] = step4_result
            current = step4_result
        
        logger.info("=" * 60)
        logger.info(f"Pipeline complete! Final image: {current}")
        logger.info("=" * 60)
        
        return current, intermediates


def run_pipeline_cli():
    """Command-line interface for the pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Avatar Realism Pipeline')
    parser.add_argument('--prompt', type=str, required=True, help='Image generation prompt')
    parser.add_argument('--aspect', type=str, default='3:4', help='Aspect ratio (1:1, 3:4, 4:3, 16:9)')
    parser.add_argument('--skip-skin', action='store_true', help='Skip skin enhancement')
    parser.add_argument('--skip-fabric', action='store_true', help='Skip fabric enhancement')
    parser.add_argument('--skip-grain', action='store_true', help='Skip grain/noise addition')
    
    args = parser.parse_args()
    
    pipeline = AvatarRealismPipeline()
    final_path, intermediates = pipeline.run_full_pipeline(
        prompt=args.prompt,
        aspect_ratio=args.aspect,
        skip_skin=args.skip_skin,
        skip_fabric=args.skip_fabric,
        skip_grain=args.skip_grain
    )
    
    print(f"\nFinal image: {final_path}")
    print(f"Intermediates: {intermediates}")
    return final_path


if __name__ == "__main__":
    run_pipeline_cli()
