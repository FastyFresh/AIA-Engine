"""
MicroMovementAgent - Generates subtle micro-movement videos from hero reference images

Supports multiple models for best face/character consistency:
- Kling v2.1: Best for face preservation and natural movements
- ConsistI2V: Designed specifically for visual consistency
- SVD: Fallback option (less consistent for faces)
"""

import os
import re
import random
import logging
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.pipeline_config import MICRO_MOVEMENT_PROMPTS


def strip_emojis(text: str) -> str:
    """Remove emoji characters from text for video overlay (FFmpeg can't render color emojis)"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002600-\U000026FF"  # misc symbols (includes ☀️)
        "\U00002700-\U000027BF"  # dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F000-\U0001F02F"  # mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # playing cards
        "\U00002300-\U000023FF"  # misc technical
        "\U00002B50"              # star
        "\U00002728"              # sparkles
        "\U0001F49C-\U0001F49F"  # heart decorations
        "\U0001F90D-\U0001F90F"  # white/brown/black hearts
        "\U00002764"              # red heart
        "\U0001F494-\U0001F49B"  # hearts
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()

logger = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

AVAILABLE_MODELS = {
    "kling": {
        "name": "Kling v2.1",
        "model_id": "kwaivgi/kling-v2.1",
        "description": "Best for face preservation and natural movements",
        "supports_prompt": True,
        "default": True
    },
    "consisti2v": {
        "name": "ConsistI2V", 
        "model_id": "wren93/consisti2v",
        "description": "Designed for visual consistency across frames",
        "supports_prompt": True,
        "default": False
    },
    "svd": {
        "name": "Stable Video Diffusion",
        "model_id": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
        "description": "General image-to-video (may distort faces)",
        "supports_prompt": False,
        "default": False
    }
}


class MicroMovementAgent:
    """Agent for generating micro-movement videos from hero reference images"""
    
    def __init__(self, default_model: str = "kling"):
        self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.output_dir = Path("content/loops")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.default_model = default_model
        
        logger.info(f"MicroMovementAgent initialized with default model: {default_model}")
    
    def get_available_models(self) -> Dict[str, Any]:
        """Return available models and their descriptions"""
        return AVAILABLE_MODELS
    
    def get_movement_prompt(self, movement_type: str) -> str:
        """Get the full prompt for a movement type"""
        return MICRO_MOVEMENT_PROMPTS.get(movement_type, MICRO_MOVEMENT_PROMPTS["micro_sway"])
    
    def list_available_movements(self) -> List[str]:
        """List all available movement types"""
        return list(MICRO_MOVEMENT_PROMPTS.keys())
    
    async def generate_loop(
        self,
        hero_image_path: str,
        influencer_handle: str,
        movement_type: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a micro-movement video from a hero reference image
        
        Args:
            hero_image_path: Path to the source hero image
            influencer_handle: The influencer's handle (e.g., "luna_vale")
            movement_type: One of the predefined movement types (random if not specified)
            custom_prompt: Optional custom prompt to use instead of predefined
            model: Model to use: "kling", "consisti2v", or "svd"
            
        Returns:
            Dict with status, output_path, and metadata
        """
        handle = influencer_handle.replace("@", "").lower()
        selected_model = model or self.default_model
        
        if selected_model not in AVAILABLE_MODELS:
            selected_model = self.default_model
        
        if not self.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return {
                "status": "error",
                "error": "REPLICATE_API_TOKEN not configured. Please add your Replicate API token.",
                "output_path": None
            }
        
        hero_path = Path(hero_image_path)
        if not hero_path.exists():
            logger.error(f"Hero image not found: {hero_image_path}")
            return {
                "status": "error", 
                "error": f"Hero image not found: {hero_image_path}",
                "output_path": None
            }
        
        if movement_type is None:
            movement_type = random.choice(self.list_available_movements())
        
        prompt = custom_prompt if custom_prompt else self.get_movement_prompt(movement_type)
        
        influencer_dir = self.output_dir / handle
        influencer_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{handle}_{movement_type}_{timestamp}.mp4"
        output_path = influencer_dir / output_filename
        
        try:
            logger.info(f"Generating loop for {handle} using {selected_model}: {movement_type}")
            
            if selected_model == "kling":
                result = await self._call_kling(
                    hero_image_path=str(hero_path),
                    prompt=prompt,
                    output_path=str(output_path)
                )
            elif selected_model == "consisti2v":
                result = await self._call_consisti2v(
                    hero_image_path=str(hero_path),
                    prompt=prompt,
                    output_path=str(output_path)
                )
            else:
                result = await self._call_svd(
                    hero_image_path=str(hero_path),
                    movement_type=movement_type,
                    output_path=str(output_path)
                )
            
            if result.get("success"):
                logger.info(f"Loop generated successfully: {output_path}")
                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "movement_type": movement_type,
                    "hero_image": str(hero_path),
                    "influencer": handle,
                    "timestamp": timestamp,
                    "model_used": selected_model,
                    "video_url": result.get("video_url")
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown error"),
                    "output_path": None,
                    "model_used": selected_model
                }
                
        except Exception as e:
            logger.error(f"Error generating loop: {e}")
            return {
                "status": "error",
                "error": str(e),
                "output_path": None
            }
    
    async def _upload_image_to_data_uri(self, image_path: str) -> str:
        """Convert local image to data URI for API calls"""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        return f"data:{mime_type};base64,{image_data}"
    
    async def _call_kling(
        self,
        hero_image_path: str,
        prompt: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Call Kling v2.1 API - excellent for face preservation
        """
        logger.info(f"Calling Kling v2.1 API with prompt: {prompt[:50]}...")
        
        image_data_uri = await self._upload_image_to_data_uri(hero_image_path)
        
        payload = {
            "input": {
                "start_image": image_data_uri,
                "prompt": prompt,
                "negative_prompt": "distorted face, blurry, deformed, morphing, inconsistent features, low quality",
                "duration": 10,
                "cfg_scale": 0.5,
                "aspect_ratio": "9:16"
            }
        }
        
        return await self._run_replicate_prediction(
            model_id=AVAILABLE_MODELS["kling"]["model_id"],
            payload=payload,
            output_path=output_path
        )
    
    async def _call_consisti2v(
        self,
        hero_image_path: str,
        prompt: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Call ConsistI2V API - designed for visual consistency
        """
        logger.info(f"Calling ConsistI2V API with prompt: {prompt[:50]}...")
        
        image_data_uri = await self._upload_image_to_data_uri(hero_image_path)
        
        payload = {
            "input": {
                "image": image_data_uri,
                "prompt": prompt,
                "negative_prompt": "inconsistent face, morphing, deformed, blurry, low quality",
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "video_guidance_scale": 3.5
            }
        }
        
        return await self._run_replicate_prediction(
            model_id=AVAILABLE_MODELS["consisti2v"]["model_id"],
            payload=payload,
            output_path=output_path
        )
    
    async def _call_svd(
        self,
        hero_image_path: str,
        movement_type: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Call Stable Video Diffusion API (fallback, less face-consistent)
        """
        logger.info(f"Calling SVD API for movement: {movement_type}")
        
        image_data_uri = await self._upload_image_to_data_uri(hero_image_path)
        
        subtle_movements = {"micro_sway", "breathing", "soft_blink", "micro_smile"}
        medium_movements = {"hair_breeze", "weight_shift", "head_tilt", "shoulder_adjust"}
        
        if movement_type in subtle_movements:
            motion_bucket = random.randint(40, 55)
        elif movement_type in medium_movements:
            motion_bucket = random.randint(50, 65)
        else:
            motion_bucket = random.randint(60, 75)
        
        payload = {
            "version": AVAILABLE_MODELS["svd"]["model_id"].split(":")[1],
            "input": {
                "input_image": image_data_uri,
                "video_length": "25_frames_with_svd_xt",
                "frames_per_second": 6,
                "sizing_strategy": "maintain_aspect_ratio",
                "motion_bucket_id": motion_bucket,
                "cond_aug": 0.0,
                "decoding_t": 7
            }
        }
        
        return await self._run_replicate_prediction(
            model_id=AVAILABLE_MODELS["svd"]["model_id"],
            payload=payload,
            output_path=output_path,
            use_version=True
        )
    
    async def _run_replicate_prediction(
        self,
        model_id: str,
        payload: Dict[str, Any],
        output_path: str,
        use_version: bool = False
    ) -> Dict[str, Any]:
        """
        Run a Replicate prediction and wait for result
        """
        headers = {
            "Authorization": f"Token {self.replicate_api_token}",
            "Content-Type": "application/json"
        }
        
        if not use_version and "version" not in payload:
            async with httpx.AsyncClient(timeout=30.0) as client:
                model_url = f"https://api.replicate.com/v1/models/{model_id}"
                model_response = await client.get(model_url, headers=headers)
                if model_response.status_code == 200:
                    model_data = model_response.json()
                    latest_version = model_data.get("latest_version", {}).get("id")
                    if latest_version:
                        payload["version"] = latest_version
                else:
                    return {"success": False, "error": f"Could not get model version: {model_response.text}"}
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                REPLICATE_API_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 201:
                error_msg = f"Replicate API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            prediction = response.json()
            prediction_id = prediction["id"]
            logger.info(f"Prediction started: {prediction_id}")
            
            status_url = f"{REPLICATE_API_URL}/{prediction_id}"
            max_attempts = 120
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(5)
                attempt += 1
                
                status_response = await client.get(status_url, headers=headers)
                status_data = status_response.json()
                status = status_data.get("status")
                
                if attempt % 6 == 0:
                    logger.info(f"Prediction status ({attempt}/{max_attempts}): {status}")
                
                if status == "succeeded":
                    output = status_data.get("output")
                    if output:
                        video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else output.get("video")
                        
                        if video_url:
                            video_response = await client.get(video_url)
                            if video_response.status_code == 200:
                                with open(output_path, "wb") as f:
                                    f.write(video_response.content)
                                logger.info(f"Video saved to: {output_path}")
                                return {
                                    "success": True,
                                    "video_url": video_url,
                                    "output_path": output_path
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": f"Failed to download video: {video_response.status_code}"
                                }
                        else:
                            return {"success": False, "error": "No video URL in output"}
                    else:
                        return {"success": False, "error": "No output in response"}
                
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    logger.error(f"Prediction failed: {error}")
                    return {"success": False, "error": f"Replicate prediction failed: {error}"}
                
                elif status == "canceled":
                    return {"success": False, "error": "Prediction was canceled"}
            
            return {"success": False, "error": "Prediction timed out after 10 minutes"}
    
    async def list_loops(
        self,
        influencer_handle: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List generated loops for an influencer"""
        handle = influencer_handle.replace("@", "").lower()
        influencer_dir = self.output_dir / handle
        
        if not influencer_dir.exists():
            return []
        
        loops = []
        for video_file in sorted(influencer_dir.glob("*.mp4"), reverse=True)[:limit]:
            stat = video_file.stat()
            parts = video_file.stem.split("_")
            
            loops.append({
                "filename": video_file.name,
                "path": str(video_file),
                "size_kb": stat.st_size // 1024,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "movement_type": parts[-2] if len(parts) >= 3 else "unknown"
            })
        
        return loops
    
    async def list_hero_refs(self, influencer_handle: str) -> List[Dict[str, Any]]:
        """List available hero reference images for an influencer"""
        handle = influencer_handle.replace("@", "").lower()
        hero_dir = Path(f"content/references/{handle}/hero")
        
        if not hero_dir.exists():
            return []
        
        refs = []
        for img_file in sorted(hero_dir.glob("*.png")) + sorted(hero_dir.glob("*.jpg")):
            stat = img_file.stat()
            refs.append({
                "filename": img_file.name,
                "path": str(img_file),
                "size_kb": stat.st_size // 1024,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return refs
    
    def _wrap_text(self, text: str, max_chars: int = 25) -> List[str]:
        """Wrap text to fit within video frame (Instagram Reels style - 25 chars max)"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line = f"{current_line} {word}".strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text[:max_chars]]
    
    def _get_video_dimensions(self, video_path: str) -> tuple:
        """Get video width and height using ffprobe"""
        import subprocess
        import json
        
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "v:0",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]
                return stream.get("width", 960), stream.get("height", 960)
        except:
            pass
        return 960, 960
    
    def _create_ass_subtitle(self, caption_lines: List[str], video_height: int, position: str = "center") -> str:
        """Create ASS subtitle content with proper formatting"""
        font_size = max(18, int(video_height * 0.038))
        
        if position == "top":
            alignment = 8
            margin_v = int(video_height * 0.08)
        elif position == "bottom":
            alignment = 2
            margin_v = int(video_height * 0.08)
        else:
            alignment = 5
            margin_v = 0
        
        wrapped_lines = []
        for line in caption_lines:
            line = strip_emojis(line)
            if not line.strip():
                wrapped_lines.append("")
            elif len(line) > 22:
                wrapped = self._wrap_text(line, max_chars=22)
                wrapped_lines.extend(wrapped)
            else:
                wrapped_lines.append(line)
        
        text_content = "\\N".join(wrapped_lines)
        
        ass_content = f"""[Script Info]
Title: Caption
ScriptType: v4.00+
PlayResX: 960
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:30.00,Default,,0,0,0,,{text_content}
"""
        return ass_content

    async def add_caption_to_video(
        self,
        video_path: str,
        caption_lines: List[str],
        position: str = "center",
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black",
        outline_width: int = 2
    ) -> Dict[str, Any]:
        """
        Add text caption overlay to a video using ASS subtitles (reliable method)
        """
        import subprocess
        import tempfile
        
        input_path = Path(video_path)
        if not input_path.exists():
            return {"success": False, "error": f"Video not found: {video_path}"}
        
        captioned_dir = self.output_dir / "captioned"
        captioned_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{input_path.stem}_captioned_{timestamp}.mp4"
        output_path = captioned_dir / output_filename
        
        width, height = self._get_video_dimensions(str(input_path))
        logger.info(f"Video dimensions: {width}x{height}")
        
        ass_content = self._create_ass_subtitle(caption_lines, height, position)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ass', delete=False) as f:
            f.write(ass_content)
            ass_path = f.name
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-vf", f"ass={ass_path}",
                "-c:a", "copy",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                str(output_path)
            ]
            
            logger.info(f"Adding caption to video: {input_path.name}")
            logger.info(f"Caption lines: {caption_lines}")
            logger.info(f"Using ASS subtitles for reliable text rendering")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return {
                    "success": False,
                    "error": f"FFmpeg failed: {result.stderr[:500]}"
                }
            
            logger.info(f"Captioned video saved: {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "original_path": str(input_path),
                "caption_lines": caption_lines,
                "position": position
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "FFmpeg timed out after 2 minutes"}
        except Exception as e:
            logger.error(f"Caption error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            try:
                Path(ass_path).unlink()
            except:
                pass
    
    async def list_captioned_videos(
        self,
        influencer_handle: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List captioned videos"""
        captioned_dir = self.output_dir / "captioned"
        
        if not captioned_dir.exists():
            return []
        
        videos = []
        for video_file in sorted(captioned_dir.glob("*.mp4"), reverse=True)[:limit]:
            if influencer_handle:
                handle = influencer_handle.replace("@", "").lower()
                if handle not in video_file.name.lower():
                    continue
                    
            stat = video_file.stat()
            videos.append({
                "filename": video_file.name,
                "path": str(video_file),
                "size_kb": stat.st_size // 1024,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return videos
    
    async def add_watermark(
        self,
        video_path: str,
        influencer: str = "starbright_monroe",
        position: str = "bottom_right"
    ) -> Dict[str, Any]:
        """
        Add watermark overlay to video (username + fanvue link)
        
        Args:
            video_path: Path to input video
            influencer: Influencer name for watermark text
            position: Position of watermark (bottom_right, bottom_left, top_right, top_left)
        """
        import subprocess
        
        # Watermark text per influencer
        watermarks = {
            "starbright_monroe": "@Starbright  fanvue.com/starbright",
            "luna_vale": "@LunaVale  fanvue.com/lunavale",
        }
        
        watermark_text = watermarks.get(influencer, watermarks["starbright_monroe"])
        
        input_path = Path(video_path)
        if not input_path.exists():
            return {"success": False, "error": f"Video not found: {video_path}"}
        
        # Output to same directory with _wm suffix
        output_path = input_path.parent / f"{input_path.stem}_wm{input_path.suffix}"
        
        width, height = self._get_video_dimensions(str(input_path))
        
        # Calculate font size (2.5% of height for subtle watermark)
        font_size = max(14, int(height * 0.025))
        
        # Position calculations
        positions = {
            "bottom_right": f"x=w-tw-20:y=h-th-15",
            "bottom_left": f"x=20:y=h-th-15",
            "top_right": f"x=w-tw-20:y=15",
            "top_left": f"x=20:y=15",
        }
        pos = positions.get(position, positions["bottom_right"])
        
        # FFmpeg drawtext filter for watermark
        drawtext_filter = (
            f"drawtext=text='{watermark_text}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={font_size}:"
            f"fontcolor=white@0.7:"
            f"borderw=1:"
            f"bordercolor=black@0.5:"
            f"{pos}"
        )
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-vf", drawtext_filter,
                "-c:a", "copy",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                str(output_path)
            ]
            
            logger.info(f"Adding watermark to video: {input_path.name}")
            logger.info(f"Watermark: {watermark_text}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg watermark error: {result.stderr}")
                return {
                    "success": False,
                    "error": f"FFmpeg failed: {result.stderr[:500]}"
                }
            
            logger.info(f"Watermarked video saved: {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "original_path": str(input_path),
                "watermark_text": watermark_text,
                "position": position
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "FFmpeg timed out after 2 minutes"}
        except Exception as e:
            logger.error(f"Watermark error: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_caption_and_watermark(
        self,
        video_path: str,
        caption_lines: List[str],
        influencer: str = "starbright_monroe",
        caption_position: str = "center",
        watermark_position: str = "bottom_right"
    ) -> Dict[str, Any]:
        """
        Add both caption overlay and watermark to video in one pass
        
        Args:
            video_path: Path to input video
            caption_lines: List of caption text lines
            influencer: Influencer name for watermark
            caption_position: Position for caption (center, top, bottom)
            watermark_position: Position for watermark (bottom_right, etc.)
        """
        import subprocess
        import tempfile
        
        # Watermark text per influencer
        watermarks = {
            "starbright_monroe": "@Starbright  fanvue.com/starbright",
            "luna_vale": "@LunaVale  fanvue.com/lunavale",
        }
        
        watermark_text = watermarks.get(influencer, watermarks["starbright_monroe"])
        
        input_path = Path(video_path)
        if not input_path.exists():
            return {"success": False, "error": f"Video not found: {video_path}"}
        
        # Output to captioned directory
        captioned_dir = self.output_dir / "captioned"
        captioned_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{input_path.stem}_full_{timestamp}.mp4"
        output_path = captioned_dir / output_filename
        
        width, height = self._get_video_dimensions(str(input_path))
        logger.info(f"Video dimensions: {width}x{height}")
        
        # Create ASS subtitle for caption
        ass_content = self._create_ass_subtitle(caption_lines, height, caption_position)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ass', delete=False) as f:
            f.write(ass_content)
            ass_path = f.name
        
        # Watermark settings
        wm_font_size = max(14, int(height * 0.025))
        positions = {
            "bottom_right": f"x=w-tw-20:y=h-th-15",
            "bottom_left": f"x=20:y=h-th-15",
            "top_right": f"x=w-tw-20:y=15",
            "top_left": f"x=20:y=15",
        }
        wm_pos = positions.get(watermark_position, positions["bottom_right"])
        
        # Combined filter: ASS subtitle + drawtext watermark
        vf_filter = (
            f"ass={ass_path},"
            f"drawtext=text='{watermark_text}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={wm_font_size}:"
            f"fontcolor=white@0.7:"
            f"borderw=1:"
            f"bordercolor=black@0.5:"
            f"{wm_pos}"
        )
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-vf", vf_filter,
                "-c:a", "copy",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                str(output_path)
            ]
            
            logger.info(f"Adding caption + watermark to video: {input_path.name}")
            logger.info(f"Caption lines: {caption_lines}")
            logger.info(f"Watermark: {watermark_text}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return {
                    "success": False,
                    "error": f"FFmpeg failed: {result.stderr[:500]}"
                }
            
            logger.info(f"Full video saved: {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "original_path": str(input_path),
                "caption_lines": caption_lines,
                "watermark_text": watermark_text,
                "influencer": influencer
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "FFmpeg timed out after 2 minutes"}
        except Exception as e:
            logger.error(f"Caption+watermark error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            try:
                Path(ass_path).unlink()
            except:
                pass
