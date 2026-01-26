import os
import httpx
import base64
import asyncio
import zipfile
import io
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GenerationModel(Enum):
    FLUX_PRO = "black-forest-labs/flux-1.1-pro"
    FLUX_KONTEXT_PRO = "black-forest-labs/flux-kontext-pro"
    FLUX_KONTEXT_MAX = "black-forest-labs/flux-kontext-max"
    INSTANT_ID = "zsxkib/instant-id"
    FACE_SWAP = "easel/advanced-face-swap"
    FACE_SWAP_SIMPLE = "codeplugtech/face-swap"
    PULID_FLUX = "bytedance/flux-pulid"
    FLUX_DEV = "black-forest-labs/flux-dev"


@dataclass
class TrainingResult:
    status: str
    training_id: Optional[str] = None
    model_name: Optional[str] = None
    trigger_word: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "training_id": self.training_id,
            "model_name": self.model_name,
            "trigger_word": self.trigger_word,
            "error": self.error,
            "logs": self.logs
        }


@dataclass
class GenerationResult:
    status: str
    image_path: Optional[str] = None
    prediction_id: Optional[str] = None
    model: Optional[str] = None
    reference_used: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "image_path": self.image_path,
            "prediction_id": self.prediction_id,
            "model": self.model,
            "reference_used": self.reference_used,
            "error": self.error
        }


class ReplicateClient:
    
    INSTANT_ID_VERSION = "2e4785a4d80dadf580077b2244c8d7c05d8e3faac04a04c02d8e099dd2876789"
    
    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        self.base_url = "https://api.replicate.com/v1"
        
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not set - Replicate client will not work")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def _check_token(self) -> Optional[Dict[str, Any]]:
        if not self.api_token:
            return {"status": "error", "message": "REPLICATE_API_TOKEN not configured"}
        return None
    
    def _encode_image_to_data_uri(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{image_data}"
    
    def _ensure_output_dir(self, output_dir: str) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def _create_prediction(
        self,
        client: httpx.AsyncClient,
        input_data: Dict[str, Any],
        model: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        if model:
            url = f"{self.base_url}/models/{model}/predictions"
            payload = {"input": input_data}
        else:
            url = f"{self.base_url}/predictions"
            payload = {"version": version, "input": input_data}
        
        response = await client.post(url, headers=self._get_headers(), json=payload)
        
        if response.status_code not in [200, 201]:
            return {
                "status": "error",
                "message": f"API error: {response.status_code}",
                "details": response.text
            }
        
        return response.json()
    
    async def _wait_for_prediction(
        self,
        client: httpx.AsyncClient,
        prediction_id: str,
        max_attempts: int = 120,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        for attempt in range(max_attempts):
            response = await client.get(
                f"{self.base_url}/predictions/{prediction_id}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get prediction status: {response.status_code}")
                return {"status": "error", "message": "Failed to check prediction status"}
            
            result = response.json()
            status = result.get("status")
            
            if status == "succeeded":
                return result
            elif status in ["failed", "canceled"]:
                return {
                    "status": status,
                    "error": result.get("error", "Unknown error")
                }
            
            logger.info(f"Prediction {prediction_id} status: {status} (attempt {attempt + 1})")
            await asyncio.sleep(poll_interval)
        
        return {"status": "error", "message": "Prediction timed out"}
    
    async def _download_image(
        self,
        client: httpx.AsyncClient,
        url: str,
        output_dir: str,
        filename_prefix: str,
        format: str = "png"
    ) -> str:
        response = await client.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download image: {response.status_code}")
        
        import time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sort_key = 9999999999 - int(time.time())
        filename = f"{sort_key}_{filename_prefix}_{timestamp}.{format}"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Image saved to: {filepath}")
        return filepath
    
    async def _run_prediction(
        self,
        input_data: Dict[str, Any],
        output_dir: str,
        filename_prefix: str,
        model: Optional[str] = None,
        version: Optional[str] = None,
        output_format: str = "png",
        timeout: float = 300.0
    ) -> GenerationResult:
        error = self._check_token()
        if error:
            return GenerationResult(status="error", error=error["message"])
        
        self._ensure_output_dir(output_dir)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                prediction = await self._create_prediction(client, input_data, model, version)
                
                if prediction.get("status") == "error":
                    return GenerationResult(
                        status="error",
                        error=prediction.get("message", "Prediction creation failed")
                    )
                
                prediction_id = prediction.get("id")
                if not prediction_id:
                    return GenerationResult(status="error", error="No prediction ID returned")
                result = await self._wait_for_prediction(client, prediction_id)
                
                if result.get("status") == "succeeded":
                    image_url = result.get("output")
                    if isinstance(image_url, list):
                        image_url = image_url[0]
                    
                    if image_url:
                        image_path = await self._download_image(
                            client, image_url, output_dir, filename_prefix, output_format
                        )
                        return GenerationResult(
                            status="success",
                            image_path=image_path,
                            prediction_id=prediction_id,
                            model=model or "versioned"
                        )
                
                return GenerationResult(
                    status="error",
                    error=result.get("error", "Prediction failed")
                )
                
        except httpx.TimeoutException:
            logger.error("Replicate API timeout")
            return GenerationResult(status="error", error="API request timed out")
        except Exception as e:
            logger.error(f"Replicate API exception: {str(e)}")
            return GenerationResult(status="error", error=str(e))

    async def generate_flux(
        self,
        prompt: str,
        model: str = GenerationModel.FLUX_PRO.value,
        aspect_ratio: str = "1:1",
        output_dir: str = "content/raw",
        filename_prefix: str = "generated"
    ) -> Dict[str, Any]:
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "output_quality": 90
        }
        
        logger.info(f"Generating FLUX image with model: {model}")
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            model=model
        )
        result.model = model
        return result.to_dict()

    async def generate_with_instant_id(
        self,
        prompt: str,
        reference_image_path: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "generated",
        guidance_scale: float = 4.0,
        ip_adapter_scale: float = 0.55,
        controlnet_scale: float = 0.4
    ) -> Dict[str, Any]:
        if not os.path.exists(reference_image_path):
            return {"status": "error", "message": f"Reference image not found: {reference_image_path}"}
        
        data_uri = self._encode_image_to_data_uri(reference_image_path)
        
        enhanced_prompt = (
            f"professional photograph of a woman, {prompt}, "
            f"hyperrealistic, photorealistic, natural skin texture with pores, "
            f"RAW photo, 8k uhd, dslr, soft lighting, high quality"
        )
        
        negative_prompt = (
            "(lowres, low quality, worst quality:1.2), (text:1.2), watermark, "
            "painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, "
            "ugly, disfigured, cartoon, anime, CGI, 3D render, digital art, "
            "artificial, plastic skin, airbrushed, multiple people, two people, "
            "ghost face, duplicate face, two heads, double head"
        )
        
        input_data = {
            "image": data_uri,
            "prompt": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": 1,
            "sdxl_weights": "RealVisXL_V4.0_Lightning",
            "scheduler": "DPMSolverMultistepScheduler-Karras",
            "num_inference_steps": 35,
            "guidance_scale": guidance_scale,
            "ip_adapter_scale": ip_adapter_scale,
            "controlnet_conditioning_scale": controlnet_scale,
            "output_format": "png",
            "output_quality": 100,
            "enable_pose_controlnet": False,
            "enhance_nonface_region": True,
            "disable_safety_checker": True
        }
        
        logger.info(f"Generating with InstantID, reference: {reference_image_path}")
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            version=self.INSTANT_ID_VERSION
        )
        result.model = GenerationModel.INSTANT_ID.value
        result.reference_used = reference_image_path
        return result.to_dict()

    async def generate_with_kontext(
        self,
        prompt: str,
        reference_image_path: str,
        model: str = GenerationModel.FLUX_KONTEXT_PRO.value,
        aspect_ratio: str = "3:4",
        output_dir: str = "content/raw",
        filename_prefix: str = "generated"
    ) -> Dict[str, Any]:
        if not os.path.exists(reference_image_path):
            return {"status": "error", "message": f"Reference image not found: {reference_image_path}"}
        
        data_uri = self._encode_image_to_data_uri(reference_image_path)
        
        enhanced_prompt = (
            f"Professional photograph of the person in the reference image, {prompt}. "
            f"Hyperrealistic, natural skin texture with visible pores, professional DSLR quality, "
            f"RAW photo, 8k uhd, soft natural lighting, sharp focus, film grain"
        )
        
        input_data = {
            "prompt": enhanced_prompt,
            "image_url": data_uri,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "safety_tolerance": 6,
            "output_quality": 100
        }
        
        logger.info(f"Generating with FLUX Kontext: {model}")
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            model=model
        )
        result.model = model
        result.reference_used = reference_image_path
        return result.to_dict()

    async def face_swap(
        self,
        target_image_path: str,
        source_face_path: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "swapped",
        hair_source: str = "target",
        upscale: bool = True,
        detailer: bool = False,
        user_gender: str = "a woman"
    ) -> Dict[str, Any]:
        if not os.path.exists(target_image_path):
            return {"status": "error", "message": f"Target image not found: {target_image_path}"}
        if not os.path.exists(source_face_path):
            return {"status": "error", "message": f"Source face not found: {source_face_path}"}
        
        target_uri = self._encode_image_to_data_uri(target_image_path)
        source_uri = self._encode_image_to_data_uri(source_face_path)
        
        input_data = {
            "target_image": target_uri,
            "swap_image": source_uri,
            "hair_source": hair_source,
            "upscale": upscale,
            "detailer": detailer,
            "user_gender": user_gender
        }
        
        logger.info(f"Face swapping with upscale={upscale}, detailer={detailer}: {source_face_path} -> {target_image_path}")
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            model=GenerationModel.FACE_SWAP.value
        )
        result.model = GenerationModel.FACE_SWAP.value
        result.reference_used = source_face_path
        return result.to_dict()

    async def face_swap_simple(
        self,
        target_image_path: str,
        source_face_path: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "swapped"
    ) -> Dict[str, Any]:
        """Simple face swap using codeplugtech model - preserves more natural skin texture"""
        if not os.path.exists(target_image_path):
            return {"status": "error", "message": f"Target image not found: {target_image_path}"}
        if not os.path.exists(source_face_path):
            return {"status": "error", "message": f"Source face not found: {source_face_path}"}
        
        target_uri = self._encode_image_to_data_uri(target_image_path)
        source_uri = self._encode_image_to_data_uri(source_face_path)
        
        input_data = {
            "input_image": target_uri,
            "swap_image": source_uri
        }
        
        logger.info(f"Simple face swap: {source_face_path} -> {target_image_path}")
        
        version = "278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34"
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            version=version
        )
        result.model = GenerationModel.FACE_SWAP_SIMPLE.value
        result.reference_used = source_face_path
        return result.to_dict()

    async def generate_with_pulid(
        self,
        prompt: str,
        reference_image_path: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "pulid",
        num_steps: int = 20,
        guidance_scale: float = 3.5,
        id_weight: float = 0.7,
        start_step: int = 0,
        true_cfg: float = 1.0
    ) -> Dict[str, Any]:
        if not os.path.exists(reference_image_path):
            return {"status": "error", "message": f"Reference image not found: {reference_image_path}"}
        
        reference_uri = self._encode_image_to_data_uri(reference_image_path)
        
        enhanced_prompt = f"{prompt}, RAW photo, 35mm film photograph, realistic human skin with visible pores and natural texture, skin imperfections, subtle skin blemishes, natural light, detailed skin pores, photorealistic skin detail, film grain, natural lighting on face"
        
        input_data = {
            "prompt": enhanced_prompt,
            "main_face_image": reference_uri,
            "num_steps": num_steps,
            "guidance_scale": guidance_scale,
            "id_weight": id_weight,
            "start_step": start_step,
            "true_cfg": true_cfg,
            "width": 896,
            "height": 1152,
            "num_outputs": 1,
            "output_format": "png",
            "output_quality": 100,
            "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, low resolution, blurry, smooth skin, plastic skin, airbrushed, overprocessed, beauty filter, softened skin, poreless, perfect skin"
        }
        
        logger.info(f"Generating with PuLID FLUX: {prompt[:80]}...")
        
        pulid_version = "8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b"
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            version=pulid_version
        )
        result.model = "bytedance/flux-pulid"
        result.reference_used = reference_image_path
        return result.to_dict()

    async def generate_with_reference(
        self,
        prompt: str,
        reference_image_path: str,
        strength: float = 0.8,
        output_dir: str = "content/raw",
        filename_prefix: str = "generated"
    ) -> Dict[str, Any]:
        return await self.generate_with_instant_id(
            prompt=prompt,
            reference_image_path=reference_image_path,
            output_dir=output_dir,
            filename_prefix=filename_prefix
        )

    async def generate_realistic_flux(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        output_dir: str = "content/raw",
        filename_prefix: str = "generated"
    ) -> Dict[str, Any]:
        enhanced_prompt = self._enhance_prompt_for_realism(prompt)
        return await self.generate_flux(
            prompt=enhanced_prompt,
            model=GenerationModel.FLUX_PRO.value,
            aspect_ratio=aspect_ratio,
            output_dir=output_dir,
            filename_prefix=filename_prefix
        )
    
    def _enhance_prompt_for_realism(self, prompt: str) -> str:
        realism_tokens = [
            "RAW photo", "35mm photograph", "natural skin texture",
            "subtle skin imperfections", "natural lighting", "photorealistic",
            "8k uhd", "dslr quality", "film grain"
        ]
        
        existing_lower = prompt.lower()
        additions = [t for t in realism_tokens if t.lower() not in existing_lower]
        
        if additions:
            return f"{prompt}, {', '.join(additions[:5])}"
        return prompt

    def _create_training_zip(self, image_paths: List[str], zip_path: str) -> bool:
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, img_path in enumerate(image_paths):
                    if os.path.exists(img_path):
                        ext = Path(img_path).suffix
                        zf.write(img_path, f"image_{i:03d}{ext}")
                        logger.info(f"Added to training zip: {img_path}")
                    else:
                        logger.warning(f"Image not found, skipping: {img_path}")
            
            zip_size = os.path.getsize(zip_path)
            logger.info(f"Created training ZIP: {zip_path} ({zip_size / 1024 / 1024:.2f} MB)")
            return True
        except Exception as e:
            logger.error(f"Failed to create training ZIP: {e}")
            return False

    async def _upload_file_to_replicate(self, file_path: str) -> Optional[str]:
        error = self._check_token()
        if error:
            return None
        
        try:
            filename = os.path.basename(file_path)
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(file_path, "rb") as f:
                    files = {
                        "content": (filename, f, "application/zip")
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/files",
                        headers={"Authorization": f"Token {self.api_token}"},
                        files=files
                    )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    file_url = result.get("urls", {}).get("get")
                    logger.info(f"Uploaded file to Replicate: {file_url}")
                    return file_url
                else:
                    logger.error(f"File upload failed: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"File upload exception: {e}")
            return None

    async def _create_model(
        self, 
        owner: str, 
        model_name: str,
        description: str = "FLUX LoRA fine-tune for AI influencer"
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                    json={
                        "owner": owner,
                        "name": model_name,
                        "visibility": "private",
                        "hardware": "gpu-t4",
                        "description": description
                    }
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Created model: {owner}/{model_name}")
                    return True
                elif response.status_code == 409:
                    logger.info(f"Model already exists: {owner}/{model_name}")
                    return True
                else:
                    logger.error(f"Failed to create model: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Create model exception: {e}")
            return False

    async def train_flux_lora(
        self,
        image_dir: str,
        model_name: str,
        trigger_word: str,
        owner: Optional[str] = None,
        training_steps: int = 3000,
        lora_rank: int = 16
    ) -> Dict[str, Any]:
        error = self._check_token()
        if error:
            return TrainingResult(status="error", error=error["message"]).to_dict()
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        image_paths = []
        
        if os.path.isdir(image_dir):
            for file in os.listdir(image_dir):
                if Path(file).suffix.lower() in image_extensions:
                    image_paths.append(os.path.join(image_dir, file))
        else:
            return TrainingResult(status="error", error=f"Directory not found: {image_dir}").to_dict()
        
        if len(image_paths) < 5:
            return TrainingResult(
                status="error", 
                error=f"Need at least 5 images for training, found {len(image_paths)}"
            ).to_dict()
        
        logger.info(f"Found {len(image_paths)} images for training")
        
        zip_path = f"/tmp/{model_name}_training.zip"
        if not self._create_training_zip(image_paths, zip_path):
            return TrainingResult(status="error", error="Failed to create training ZIP").to_dict()
        
        logger.info("Uploading training images to Replicate...")
        file_url = await self._upload_file_to_replicate(zip_path)
        
        if not file_url:
            return TrainingResult(status="error", error="Failed to upload training images").to_dict()
        
        account_owner: Optional[str] = owner
        if not account_owner:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{self.base_url}/account",
                        headers=self._get_headers()
                    )
                    if response.status_code == 200:
                        account_owner = response.json().get("username")
                        logger.info(f"Using account username: {account_owner}")
            except Exception as e:
                logger.error(f"Failed to get account info: {e}")
                return TrainingResult(status="error", error="Could not determine Replicate username").to_dict()
        
        if not account_owner:
            return TrainingResult(status="error", error="Could not determine Replicate username").to_dict()
        
        destination = f"{account_owner}/{model_name}"
        
        if not await self._create_model(account_owner, model_name):
            logger.warning(f"Could not create model, but will try training anyway")
        
        training_input = {
            "input_images": file_url,
            "trigger_word": trigger_word,
            "steps": training_steps,
            "lora_rank": lora_rank,
            "autocaption": True
        }
        
        FLUX_LORA_TRAINER_VERSION = "4ffd32160efd92e956d39c5338a9b8fbafca58e03f791f6d8011f3e20e8ea6fa"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/ostris/flux-dev-lora-trainer/versions/{FLUX_LORA_TRAINER_VERSION}/trainings",
                    headers=self._get_headers(),
                    json={
                        "destination": destination,
                        "input": training_input
                    }
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    training_id = result.get("id")
                    
                    logger.info(f"Training started! ID: {training_id}")
                    logger.info(f"Model will be available at: {destination}")
                    logger.info(f"Trigger word: {trigger_word}")
                    
                    return TrainingResult(
                        status="training_started",
                        training_id=training_id,
                        model_name=destination,
                        trigger_word=trigger_word
                    ).to_dict()
                else:
                    error_detail = response.text
                    logger.error(f"Training creation failed: {response.status_code} - {error_detail}")
                    return TrainingResult(
                        status="error", 
                        error=f"Training creation failed: {error_detail}"
                    ).to_dict()
                    
        except Exception as e:
            logger.error(f"Training exception: {e}")
            return TrainingResult(status="error", error=str(e)).to_dict()
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    async def get_training_status(self, training_id: str) -> Dict[str, Any]:
        error = self._check_token()
        if error:
            return TrainingResult(status="error", error=error["message"]).to_dict()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/trainings/{training_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    logs = result.get("logs", "")
                    
                    model_info = result.get("output", {})
                    model_name = None
                    if isinstance(model_info, dict):
                        model_name = model_info.get("version")
                    
                    return {
                        "status": status,
                        "training_id": training_id,
                        "model_name": model_name,
                        "logs": logs[-2000:] if logs else None,
                        "created_at": result.get("created_at"),
                        "completed_at": result.get("completed_at"),
                        "error": result.get("error")
                    }
                else:
                    return TrainingResult(
                        status="error",
                        error=f"Failed to get training status: {response.status_code}"
                    ).to_dict()
                    
        except Exception as e:
            logger.error(f"Get training status exception: {e}")
            return TrainingResult(status="error", error=str(e)).to_dict()

    async def generate_with_lora(
        self,
        prompt: str,
        model_name: str,
        trigger_word: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "lora_generated",
        aspect_ratio: str = "3:4",
        num_inference_steps: int = 30,
        guidance_scale: float = 2.5,
        lora_scale: float = 0.77,
        positive_prompt_additions: Optional[List[str]] = None,
        negative_prompt_additions: Optional[List[str]] = None,
        generation_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if generation_params:
            lora_scale = generation_params.get("lora_scale", lora_scale)
            guidance_scale = generation_params.get("guidance_scale", guidance_scale)
            num_inference_steps = generation_params.get("num_inference_steps", num_inference_steps)
            aspect_ratio = generation_params.get("aspect_ratio", aspect_ratio)
            positive_prompt_additions = generation_params.get("positive_prompt_additions", positive_prompt_additions)
            negative_prompt_additions = generation_params.get("negative_prompt_additions", negative_prompt_additions)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                model_response = await client.get(
                    f"{self.base_url}/models/{model_name}",
                    headers=self._get_headers()
                )
                model_response.raise_for_status()
                model_data = model_response.json()
            
            latest_version = model_data.get("latest_version", {}).get("id")
            if not latest_version:
                return {"status": "error", "error": f"No version found for model {model_name}"}
            
            logger.info(f"Found latest version for {model_name}: {latest_version[:20]}...")
            
        except Exception as e:
            logger.error(f"Failed to get model version: {str(e)}")
            return {"status": "error", "error": f"Failed to get model info: {str(e)}"}
        
        if trigger_word.lower() not in prompt.lower():
            prompt = f"{trigger_word} {prompt}"
        
        base_positive = (
            f"{prompt}, 19 year old young woman, youthful face, "
            f"editorial photograph, candid photo, iPhone photo aesthetic, "
            f"natural matte skin, powder finish complexion, no shine, "
            f"real human skin texture with pores and blemishes, "
            f"subsurface scattering, realistic skin with fine lines, "
            f"unretouched skin, natural imperfections, slight asymmetry, "
            f"RAW unedited photo, real person, documentary photography, "
            f"soft diffused lighting, shallow depth of field, "
            f"clear eyes, authentic look, no makeup filter, no glow"
        )
        
        if positive_prompt_additions:
            enhanced_prompt = f"{base_positive}, {', '.join(positive_prompt_additions)}"
        else:
            enhanced_prompt = base_positive
        
        base_negative = (
            "waxy, wax figure, plastic, silicone, mannequin, doll, CGI, "
            "3D render, video game, digital art, illustration, painting, "
            "smooth skin, poreless, airbrushed, retouched, photoshopped, "
            "beauty filter, glamour lighting, studio lighting, perfect skin, "
            "glossy, shiny, oily, sweaty, wet skin, specular highlights, "
            "symmetrical face, too perfect, uncanny valley, fake, artificial, "
            "eye infection, sty, stye, swollen eye, red eye, "
            "blotchy skin, uneven skin, mask-like, overly smooth"
        )
        
        if negative_prompt_additions:
            negative_prompt = f"{base_negative}, {', '.join(negative_prompt_additions)}"
        else:
            negative_prompt = base_negative
        
        input_data = {
            "prompt": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "output_format": "png",
            "output_quality": 100,
            "lora_scale": lora_scale
        }
        
        logger.info(f"Generating with LoRA model: {model_name}")
        logger.info(f"Prompt: {enhanced_prompt[:100]}...")
        
        result = await self._run_prediction(
            input_data=input_data,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            version=latest_version
        )
        result.model = model_name
        return result.to_dict()

    async def list_trainings(self) -> List[Dict[str, Any]]:
        error = self._check_token()
        if error:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/trainings",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    trainings = result.get("results", [])
                    
                    return [
                        {
                            "id": t.get("id"),
                            "status": t.get("status"),
                            "model": t.get("model"),
                            "destination": t.get("destination"),
                            "created_at": t.get("created_at"),
                            "completed_at": t.get("completed_at")
                        }
                        for t in trainings[:10]
                    ]
                else:
                    logger.error(f"Failed to list trainings: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"List trainings exception: {e}")
            return []
