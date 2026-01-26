from typing import Any, Dict, Optional
from datetime import datetime
from app.agents.base import BaseAgent
from app.config import InfluencerConfig
from app.tools.replicate_client import ReplicateClient
from app.tools.grok_client import GrokClient
from app.services.content_service import ContentService


class ReferenceAgent(BaseAgent):
    
    def __init__(self):
        super().__init__("ReferenceAgent")
        self.replicate_client = ReplicateClient()
        self.grok_client = GrokClient()
        self.content_service = ContentService()
    
    async def run(
        self,
        influencer: InfluencerConfig,
        identity_context: Dict[str, Any],
        use_reference: bool = True,
        generation_method: str = "instant_id"
    ) -> Dict[str, Any]:
        self.log(f"Generating content for {influencer.name} using {generation_method}")
        
        today = datetime.now().strftime("%Y-%m-%d")
        content_items = []
        generated_images = []
        
        output_dir = self.content_service.get_output_dir(influencer)
        reference_image = self.content_service.get_reference_image(influencer) if use_reference else None
        
        if reference_image:
            self.log(f"Using reference image: {reference_image}")
        else:
            self.log("No reference image found - generating without face lock")
        
        slots = self.content_service.get_daily_slots(influencer)
        
        for slot, description in slots.items():
            prompt = self.content_service.build_prompt(influencer, description, identity_context)
            filename_prefix = self.content_service.get_filename_prefix(influencer, slot)
            
            self.log(f"Generating image for {slot}: {description}")
            
            result = await self._generate_image(
                prompt=prompt,
                reference_image=reference_image,
                output_dir=output_dir,
                filename_prefix=filename_prefix,
                method=generation_method
            )
            
            content_item = {
                "slot": slot,
                "description": description,
                "influencer": influencer.name,
                "prompt": prompt,
                "generation_status": result["status"],
                "image_path": result.get("image_path"),
                "reference_used": reference_image,
                "model": result.get("model", "unknown"),
                "caption": self.content_service.generate_caption(influencer, description, identity_context)
            }
            
            content_items.append(content_item)
            
            if result["status"] == "success":
                generated_images.append(result["image_path"])
                self.log(f"SUCCESS: Image saved to {result['image_path']}")
            else:
                self.log(f"FAILED: {result.get('error', 'Unknown error')}", level="error")
        
        result = {
            "influencer": influencer.name,
            "date": today,
            "content_count": len(content_items),
            "images_generated": len(generated_images),
            "content_items": content_items,
            "generated_images": generated_images,
            "reference_image": reference_image,
            "generation_method": generation_method,
            "status": "content_generated" if generated_images else "generation_failed"
        }
        
        self.log(f"Content generation complete: {len(generated_images)}/{len(content_items)} images generated")
        return result
    
    async def _generate_image(
        self,
        prompt: str,
        reference_image: Optional[str],
        output_dir: str,
        filename_prefix: str,
        method: str = "instant_id"
    ) -> Dict[str, Any]:
        if method == "flux":
            return await self.replicate_client.generate_realistic_flux(
                prompt=prompt,
                output_dir=output_dir,
                filename_prefix=filename_prefix
            )
        
        if method == "grok":
            return await self.grok_client.generate_image(
                prompt=prompt,
                output_dir=output_dir,
                filename_prefix=filename_prefix
            )
        
        if method == "two_stage":
            return await self._generate_two_stage(
                prompt=prompt,
                reference_image=reference_image,
                output_dir=output_dir,
                filename_prefix=filename_prefix
            )
        
        if method == "pulid":
            if not reference_image:
                self.log("PuLID requires a reference image - falling back to FLUX")
                return await self.replicate_client.generate_realistic_flux(
                    prompt=prompt,
                    output_dir=output_dir,
                    filename_prefix=filename_prefix
                )
            return await self.replicate_client.generate_with_pulid(
                prompt=prompt,
                reference_image_path=reference_image,
                output_dir=output_dir,
                filename_prefix=filename_prefix
            )
        
        if reference_image:
            if method == "kontext":
                return await self.replicate_client.generate_with_kontext(
                    prompt=prompt,
                    reference_image_path=reference_image,
                    output_dir=output_dir,
                    filename_prefix=filename_prefix
                )
            else:
                return await self.replicate_client.generate_with_instant_id(
                    prompt=prompt,
                    reference_image_path=reference_image,
                    output_dir=output_dir,
                    filename_prefix=filename_prefix
                )
        else:
            return await self.replicate_client.generate_realistic_flux(
                prompt=prompt,
                output_dir=output_dir,
                filename_prefix=filename_prefix
            )
    
    async def _generate_two_stage(
        self,
        prompt: str,
        reference_image: Optional[str],
        output_dir: str,
        filename_prefix: str
    ) -> Dict[str, Any]:
        self.log("Stage 1: Generating base image with Grok Aurora")
        
        base_result = await self.grok_client.generate_image(
            prompt=prompt,
            output_dir=output_dir,
            filename_prefix=f"{filename_prefix}_base"
        )
        
        if base_result["status"] != "success":
            self.log(f"Stage 1 failed: {base_result.get('message')}", level="error")
            return base_result
        
        base_image_path = base_result["image_path"]
        self.log(f"Stage 1 complete: {base_image_path}")
        
        if not reference_image:
            self.log("No reference image for face swap - returning base image")
            return base_result
        
        self.log("Stage 2: Applying face swap")
        
        swap_result = await self.replicate_client.face_swap(
            target_image_path=base_image_path,
            source_face_path=reference_image,
            output_dir=output_dir,
            filename_prefix=f"{filename_prefix}_final"
        )
        
        if swap_result["status"] != "success":
            self.log(f"Stage 2 failed: {swap_result.get('error')}", level="error")
            return {
                "status": "partial",
                "image_path": base_image_path,
                "base_image": base_image_path,
                "swap_error": swap_result.get("error"),
                "model": "grok_aurora + face_swap_failed"
            }
        
        self.log(f"Stage 2 complete: {swap_result['image_path']}")
        
        return {
            "status": "success",
            "image_path": swap_result["image_path"],
            "base_image": base_image_path,
            "model": "grok_aurora + face_swap",
            "reference_used": reference_image
        }
    
    async def generate_single(
        self,
        influencer: InfluencerConfig,
        prompt: str,
        use_reference: bool = True,
        method: str = "instant_id"
    ) -> Dict[str, Any]:
        output_dir = self.content_service.get_output_dir(influencer)
        reference_image = self.content_service.get_reference_image(influencer) if use_reference else None
        filename_prefix = self.content_service.get_filename_prefix(influencer, "single")
        
        full_prompt = self.content_service.build_prompt(influencer, prompt)
        self.log(f"Built prompt with physical description for {influencer.name}")
        
        return await self._generate_image(
            prompt=full_prompt,
            reference_image=reference_image,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            method=method
        )
    
    def get_reference_status(self) -> Dict[str, Any]:
        return self.content_service.get_reference_status()
    
    async def generate_lora_image(
        self,
        influencer: InfluencerConfig,
        prompt: str,
        num_images: int = 1
    ) -> Dict[str, Any]:
        """
        Generate images using trained LoRA model for consistent identity.
        This is the primary generation method for the pipeline.
        
        The prompt is enriched with influencer physical descriptors for better consistency.
        Trigger word injection and prompt enhancement are handled by replicate_client.
        """
        TRAINED_MODELS = {
            "luna vale": {
                "model": "fastyfresh/luna_vale-flux-lora",
                "trigger_word": "LUNAVALE"
            },
            "starbright monroe": {
                "model": "fastyfresh/starbright_monroe-flux-lora",
                "trigger_word": "STARBRIGHTMONROE"
            }
        }
        
        GENERATION_PARAMS = {
            "Luna Vale": {
                "lora_scale": 0.77,
                "guidance_scale": 2.5,
                "num_inference_steps": 30
            },
            "Starbright Monroe": {
                "lora_scale": 1.0,
                "guidance_scale": 3.0,
                "num_inference_steps": 40,
                "aspect_ratio": "9:16",
                "positive_prompt_additions": [
                    "19 year old woman", "youthful face", "soft innocent expression",
                    "very soft rounded facial features", "full soft cheeks", "very soft jawline",
                    "baby face", "gentle soft eyes", "soft eye makeup",
                    "natural freckles scattered across cheeks and nose",
                    "long straight dark brown hair", "long silky straight hair", "perfectly straight hair",
                    "dark brown eyes", "soft gentle expression",
                    "realistic skin texture", "natural pores", "imperfect skin", "natural blemishes",
                    "matte skin finish", "non-shiny skin", "photography studio lighting",
                    "shot on Canon EOS R5 85mm f/1.4", "soft diffused daylight",
                    "authentic candid moment", "real person photography", "photorealistic"
                ],
                "negative_prompt_additions": [
                    "wavy hair", "curly hair", "messy hair", "frizzy hair", "volumized hair",
                    "glossy skin", "shiny skin", "oily skin", "wet skin", "dewy skin",
                    "airbrushed", "CGI", "plastic skin", "over-smooth", "wax figure",
                    "angular face", "sharp jawline", "chiseled features", "mature face",
                    "heavy makeup", "intense expression", "serious expression"
                ]
            }
        }
        
        trained_info = TRAINED_MODELS.get(influencer.name.lower())
        if not trained_info:
            self.log(f"No trained LoRA model for {influencer.name}", level="error")
            return {
                "status": "error",
                "error": f"No trained LoRA model for {influencer.name}"
            }
        
        model = trained_info["model"]
        trigger_word = trained_info["trigger_word"]
        params = GENERATION_PARAMS.get(influencer.name, {})
        
        output_dir = self.content_service.get_output_dir(influencer)
        filename_prefix = f"{influencer.handle.replace('@', '')}_lora"
        
        enriched_prompt = self.content_service.build_prompt(influencer, prompt)
        if trigger_word.lower() not in enriched_prompt.lower():
            enriched_prompt = f"{trigger_word} {enriched_prompt}"
        
        self.log(f"Generating LoRA image for {influencer.name}")
        self.log(f"Model: {model}, Prompt: {enriched_prompt[:100]}...")
        
        images = []
        for i in range(num_images):
            try:
                import uuid
                unique_prefix = f"{filename_prefix}_{uuid.uuid4().hex[:8]}"
                
                result = await self.replicate_client.generate_with_lora(
                    prompt=enriched_prompt,
                    model_name=model,
                    trigger_word=trigger_word,
                    output_dir=output_dir,
                    filename_prefix=unique_prefix,
                    generation_params=params
                )
                
                if result.get("status") == "success":
                    image_path = result.get("image_path")
                    if image_path:
                        images.append({
                            "path": image_path,
                            "image_path": image_path,
                            "model": model,
                            "trigger_word": trigger_word,
                            "prediction_id": result.get("prediction_id")
                        })
                        self.log(f"LoRA image generated: {image_path}")
                    else:
                        self.log(f"LoRA generation succeeded but no image path returned", level="warning")
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.log(f"LoRA generation failed: {error_msg}", level="error")
                    
            except Exception as e:
                self.log(f"LoRA generation error: {e}", level="error")
        
        return {
            "status": "success" if images else "error",
            "images": images,
            "model": model,
            "trigger_word": trigger_word,
            "prompt": enriched_prompt,
            "error": None if images else "No images generated"
        }
