import os
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GrokClient:
    
    MODEL = "grok-2-image-1212"
    BASE_URL = "https://api.x.ai/v1"
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not set - Grok client will not work")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _ensure_output_dir(self, output_dir: str) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def generate_image(
        self,
        prompt: str,
        n: int = 1,
        output_dir: str = "content/raw",
        filename_prefix: str = "grok_generated"
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "error",
                "message": "XAI_API_KEY not configured"
            }
        
        self._ensure_output_dir(output_dir)
        
        photorealistic_prompt = self._enhance_prompt(prompt)
        
        payload = {
            "model": self.MODEL,
            "prompt": photorealistic_prompt,
            "n": n
        }
        
        logger.info(f"Generating Grok Aurora image: {prompt[:100]}...")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/images/generations",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Grok API error: {response.status_code} - {error_text}")
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": error_text
                    }
                
                result = response.json()
                
                if "data" in result and len(result["data"]) > 0:
                    image_url = result["data"][0].get("url")
                    
                    if image_url:
                        image_path = await self._download_image(
                            client, image_url, output_dir, filename_prefix
                        )
                        
                        return {
                            "status": "success",
                            "image_path": image_path,
                            "model": self.MODEL,
                            "prompt_used": photorealistic_prompt
                        }
                
                return {
                    "status": "error",
                    "message": "No image URL in response"
                }
                
        except httpx.TimeoutException:
            logger.error("Grok API timeout")
            return {"status": "error", "message": "API request timed out"}
        except Exception as e:
            logger.error(f"Grok API exception: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _download_image(
        self,
        client: httpx.AsyncClient,
        url: str,
        output_dir: str,
        filename_prefix: str
    ) -> str:
        response = await client.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download image: {response.status_code}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Grok image saved to: {filepath}")
        return filepath
    
    def _enhance_prompt(self, prompt: str) -> str:
        realism_tokens = [
            "professional photograph",
            "photorealistic",
            "natural lighting",
            "8k quality",
            "detailed skin texture"
        ]
        
        existing_lower = prompt.lower()
        additions = [t for t in realism_tokens if t.lower() not in existing_lower]
        
        if additions:
            return f"{prompt}, {', '.join(additions[:3])}"
        return prompt
