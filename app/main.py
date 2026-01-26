from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Form, Body, Header, Depends
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
from pathlib import Path
from pydantic import BaseModel
import logging
import os
import subprocess
import json

from app.orchestrator import Orchestrator
from app.services.content_service import ContentService
from app.config import INFLUENCERS
from app.tools.replicate_client import ReplicateClient
from app.agents.micro_movement_agent import MicroMovementAgent
from app.pipeline_config import MICRO_MOVEMENT_PROMPTS
from app.routes.content_admin import router as content_admin_router
from app.api.admin_routes import router as admin_router
from app.api.payment_routes import router as payment_router
from app.api.telegram_api_routes import router as telegram_api_router
from app.api.micro_loop_routes import router as micro_loop_router
from app.api.webchat_routes import router as webchat_router
from app.api.gallery_routes import router as gallery_router
from app.api.twitter_routes import router as twitter_router
from app.api.seedream4_routes import router as seedream4_router
from app.api.unified_routes import router as unified_router
from app.api.workflow_routes import router as workflow_router
from app.api.object_storage_routes import router as object_storage_router, uploads_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIA Engine v1",
    description="Autonomous AI Influencer Agent Engine - Replit Hub Edition",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

content_dirs = ["content/generated", "content/loops", "content/references", "content/final", "content/training", "content/telegram"]
for dir_path in content_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

app.include_router(content_admin_router)
app.include_router(admin_router)
app.include_router(payment_router)
app.include_router(telegram_api_router)
app.include_router(micro_loop_router)
app.include_router(webchat_router)
app.include_router(gallery_router)
app.include_router(twitter_router)
app.include_router(seedream4_router)
app.include_router(unified_router)
app.include_router(workflow_router)
app.include_router(object_storage_router)
app.include_router(uploads_router)

orchestrator = Orchestrator()
content_service = ContentService()
replicate_client = ReplicateClient()
micro_movement_agent = MicroMovementAgent()


@app.get("/")
async def root():
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/", status_code=302)

@app.get("/upload")
async def upload_page():
    """Simple upload page for Telegram content"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Content - AIA Engine</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; min-height: 100vh; color: #fff; padding: 40px 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { font-size: 28px; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #aaa; font-size: 14px; }
            select, input[type="file"] { width: 100%; padding: 12px; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; color: #fff; font-size: 16px; }
            select:focus, input:focus { outline: none; border-color: #f093fb; }
            .upload-area { border: 2px dashed #333; border-radius: 12px; padding: 40px; text-align: center; margin-bottom: 20px; cursor: pointer; transition: all 0.3s; }
            .upload-area:hover { border-color: #f093fb; background: rgba(240, 147, 251, 0.05); }
            .upload-area.dragover { border-color: #f093fb; background: rgba(240, 147, 251, 0.1); }
            .upload-icon { font-size: 48px; margin-bottom: 10px; }
            .upload-text { color: #888; }
            .btn { display: inline-block; background: linear-gradient(90deg, #f093fb, #f5576c); color: white; padding: 14px 40px; border-radius: 8px; border: none; font-size: 16px; font-weight: 600; cursor: pointer; width: 100%; }
            .btn:hover { opacity: 0.9; }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; }
            .result { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
            .result.success { background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; color: #22c55e; }
            .result.error { background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #ef4444; }
            .file-list { margin-top: 30px; }
            .file-item { background: #1a1a1a; padding: 12px 15px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
            .file-name { font-size: 14px; }
            .file-size { color: #888; font-size: 12px; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #f093fb; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/dashboard/" class="back-link">← Back to Dashboard</a>
            <h1>Upload Telegram Content</h1>
            
            <form id="uploadForm">
                <div class="form-group">
                    <label>Persona</label>
                    <select id="persona">
                        <option value="starbright_monroe">Starbright Monroe</option>
                        <option value="luna_vale">Luna Vale</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Content Type</label>
                    <select id="contentType">
                        <option value="videos">Videos (Exclusive content)</option>
                        <option value="welcome_pack">Welcome Pack</option>
                        <option value="teaser">Teaser (Free users)</option>
                        <option value="photos">Photos</option>
                    </select>
                </div>
                
                <div class="upload-area" id="dropZone">
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">Click to select files or drag & drop</div>
                    <input type="file" id="fileInput" multiple accept="video/*,image/*" style="display: none;">
                </div>
                
                <button type="submit" class="btn" id="uploadBtn" disabled>Upload Files</button>
            </form>
            
            <div class="result" id="result"></div>
            
            <div class="file-list" id="fileList"></div>
        </div>
        
        <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const uploadBtn = document.getElementById('uploadBtn');
            const result = document.getElementById('result');
            const fileList = document.getElementById('fileList');
            let selectedFiles = [];
            
            dropZone.addEventListener('click', () => fileInput.click());
            dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                handleFiles(e.dataTransfer.files);
            });
            fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
            
            function handleFiles(files) {
                selectedFiles = Array.from(files);
                uploadBtn.disabled = selectedFiles.length === 0;
                dropZone.querySelector('.upload-text').textContent = selectedFiles.length + ' file(s) selected';
            }
            
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                uploadBtn.disabled = true;
                uploadBtn.textContent = 'Uploading...';
                
                const persona = document.getElementById('persona').value;
                const contentType = document.getElementById('contentType').value;
                let successCount = 0;
                
                for (const file of selectedFiles) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        const res = await fetch(`/api/telegram/upload-content?persona=${persona}&content_type=${contentType}`, {
                            method: 'POST',
                            body: formData
                        });
                        if (res.ok) successCount++;
                    } catch (err) { console.error(err); }
                }
                
                result.style.display = 'block';
                result.className = 'result success';
                result.textContent = `Successfully uploaded ${successCount} of ${selectedFiles.length} files!`;
                
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload Files';
                selectedFiles = [];
                dropZone.querySelector('.upload-text').textContent = 'Click to select files or drag & drop';
                
                loadExistingFiles();
            });
            
            async function loadExistingFiles() {
                const persona = document.getElementById('persona').value;
                const contentType = document.getElementById('contentType').value;
                const res = await fetch(`/api/telegram/content?persona=${persona}&content_type=${contentType}`);
                const data = await res.json();
                
                fileList.innerHTML = '<h3 style="margin-bottom: 15px; color: #aaa;">Existing Files</h3>';
                if (data.files.length === 0) {
                    fileList.innerHTML += '<p style="color: #666;">No files uploaded yet</p>';
                } else {
                    data.files.forEach(f => {
                        fileList.innerHTML += `<div class="file-item"><span class="file-name">${f.filename}</span><span class="file-size">${f.size_kb} KB</span></div>`;
                    });
                }
            }
            
            document.getElementById('persona').addEventListener('change', loadExistingFiles);
            document.getElementById('contentType').addEventListener('change', loadExistingFiles);
            loadExistingFiles();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/landing")
async def landing():
    """Landing page with business information for Stripe verification"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Firepie LLC - Digital Content Services</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; padding: 60px 20px; text-align: center; }
            .logo { font-size: 48px; margin-bottom: 10px; }
            h1 { font-size: 36px; margin-bottom: 10px; background: linear-gradient(90deg, #f093fb, #f5576c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .company { font-size: 18px; color: #888; margin-bottom: 40px; }
            .tagline { font-size: 20px; color: #ccc; margin-bottom: 40px; line-height: 1.6; }
            .features { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-bottom: 40px; }
            .feature { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; width: 200px; }
            .feature-icon { font-size: 32px; margin-bottom: 10px; }
            .feature-title { font-weight: 600; margin-bottom: 5px; }
            .feature-desc { font-size: 14px; color: #999; }
            .cta { display: inline-block; background: linear-gradient(90deg, #f093fb, #f5576c); color: white; padding: 15px 40px; border-radius: 30px; text-decoration: none; font-weight: 600; margin-bottom: 40px; }
            .cta:hover { opacity: 0.9; }
            footer { color: #666; font-size: 14px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 30px; }
            footer a { color: #888; text-decoration: none; margin: 0 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">✨</div>
            <h1>Exclusive AI Influencer Experience</h1>
            <p class="company">A Firepie LLC Service</p>
            <p class="tagline">Connect with AI-powered personalities through personalized conversations. Premium subscription content delivered via Telegram.</p>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">💬</div>
                    <div class="feature-title">AI Conversations</div>
                    <div class="feature-desc">Natural, personalized chats</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📸</div>
                    <div class="feature-title">Exclusive Content</div>
                    <div class="feature-desc">Premium photos & videos</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">⭐</div>
                    <div class="feature-title">VIP Access</div>
                    <div class="feature-desc">Unlimited messaging</div>
                </div>
            </div>
            
            <a href="/dashboard" class="cta">Access Dashboard</a>
            
            <footer>
                <p><strong>Firepie LLC</strong></p>
                <p style="margin-top: 10px;">
                    <a href="/terms">Terms of Service</a> |
                    <a href="/privacy">Privacy Policy</a> |
                    <a href="mailto:support@firepie.com">Contact</a>
                </p>
                <p style="margin-top: 20px;">&copy; 2024 Firepie LLC. All rights reserved.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health_check():
    import os
    
    llm_status = {}
    try:
        from app.tools.llm_client import LLMClient
        llm_client = LLMClient()
        llm_status = llm_client.get_status()
    except Exception as e:
        llm_status = {"error": str(e)}
    
    quality_status = {}
    try:
        quality_status = quality_agent.get_status()
    except Exception as e:
        quality_status = {"error": str(e)}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AIA Engine v1.6",
        "agents": {
            "IdentityAgent": "active",
            "ReferenceAgent": "active",
            "QualityAgent": "active",
            "EditingAgent": "disabled",
            "PostingAgent": "disabled",
            "FanvueFunnelAgent": "disabled",
            "AnalyticsAgent": "disabled"
        },
        "api_keys": {
            "REPLICATE_API_TOKEN": "configured" if os.getenv("REPLICATE_API_TOKEN") else "missing",
            "XAI_API_KEY": "configured" if os.getenv("XAI_API_KEY") else "missing",
            "ANTHROPIC_API_KEY": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing",
            "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") else "missing"
        },
        "llm": llm_status,
        "quality": quality_status
    }


class DailyCycleRequest(BaseModel):
    method: str = "instant_id"
    use_reference: bool = True
    use_pipeline: bool = False
    dry_run: bool = False
    skip_posting: bool = False


@app.get("/daily_cycle")
async def run_daily_cycle_get(
    method: str = Query(default="instant_id", description="Generation method: instant_id, kontext, or flux"),
    use_reference: bool = Query(default=True, description="Use reference images if available"),
    use_pipeline: bool = Query(default=False, description="Use full automation pipeline (generate + package + post)"),
    dry_run: bool = Query(default=False, description="Dry run mode - simulate without API calls"),
    skip_posting: bool = Query(default=False, description="Skip posting to social platforms")
):
    """GET handler for daily cycle (backwards compatibility)"""
    return await _run_daily_cycle(method, use_reference, use_pipeline, dry_run, skip_posting)


@app.post("/daily_cycle")
async def run_daily_cycle_post(request: DailyCycleRequest = None):
    """POST handler for daily cycle (frontend dashboard)"""
    if request is None:
        request = DailyCycleRequest()
    return await _run_daily_cycle(
        request.method, 
        request.use_reference, 
        request.use_pipeline, 
        request.dry_run,
        request.skip_posting
    )


async def _run_daily_cycle(
    method: str, 
    use_reference: bool, 
    use_pipeline: bool = False, 
    dry_run: bool = False,
    skip_posting: bool = False
):
    """Shared daily cycle logic for GET and POST handlers"""
    logger.info(f"Daily cycle triggered: method={method}, use_reference={use_reference}, pipeline={use_pipeline}, dry_run={dry_run}")
    
    try:
        if use_pipeline:
            result = await pipeline_orchestrator.run_daily_pipeline(
                dry_run=dry_run,
                skip_posting=skip_posting
            )
        else:
            result = await orchestrator.run_daily_cycle(
                generation_method=method,
                use_reference=use_reference
            )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Daily cycle failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate")
async def generate_single(
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    prompt: Optional[str] = Query(default=None, description="Custom prompt"),
    method: str = Query(default="instant_id", description="Generation method: instant_id, kontext, or flux"),
    use_reference: bool = Query(default=True, description="Use reference image")
):
    logger.info(f"Single generation for {influencer}: method={method}")
    
    try:
        if not prompt:
            inf_config = None
            for inf in INFLUENCERS:
                if inf.name.lower() == influencer.lower():
                    inf_config = inf
                    break
            
            if inf_config:
                prompt = f"professional fashion photography, {inf_config.aesthetic}"
            else:
                prompt = "professional photography, natural lighting"
        
        result = await orchestrator.generate_single(
            influencer_name=influencer,
            prompt=prompt,
            method=method,
            use_reference=use_reference
        )
        
        return {
            "influencer": influencer,
            "prompt": prompt,
            "method": method,
            "use_reference": use_reference,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Single generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/references")
async def check_references():
    status = content_service.get_reference_status()
    
    return {
        "reference_path": "content/references/",
        "instructions": "Upload reference images to content/references/{influencer_name}/ for face/body consistency",
        "supported_formats": ["png", "jpg", "jpeg", "webp"],
        "influencer_status": status
    }


@app.get("/influencers")
async def list_influencers():
    return {
        "count": len(INFLUENCERS),
        "influencers": [
            {
                "name": inf.name,
                "handle": inf.handle,
                "niche": inf.niche,
                "aesthetic": inf.aesthetic,
                "fanvue_tier": inf.fanvue_tier,
                "has_reference": content_service.get_reference_image(inf) is not None
            }
            for inf in INFLUENCERS
        ]
    }


@app.get("/daily_cycle_flux")
async def run_daily_cycle_flux(
    use_reference: bool = Query(default=True, description="Use reference images")
):
    return await _run_daily_cycle(method="flux", use_reference=use_reference)


@app.get("/test_face_reference")
async def test_face_reference(
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    prompt: Optional[str] = Query(default=None, description="Custom prompt")
):
    return await generate_single(
        influencer=influencer,
        prompt=prompt,
        method="instant_id",
        use_reference=True
    )


@app.get("/test_kontext")
async def test_kontext(
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    prompt: Optional[str] = Query(default=None, description="Custom prompt")
):
    return await generate_single(
        influencer=influencer,
        prompt=prompt,
        method="kontext",
        use_reference=True
    )


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

@app.get("/train")
async def train_lora(
    influencer: str = Query(default="Luna Vale", description="Influencer to train"),
    trigger_word: Optional[str] = Query(default=None, description="Unique trigger word"),
    steps: int = Query(default=3000, description="Training steps (3000 for full convergence)")
):
    logger.info(f"LoRA training requested for {influencer}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    reference_dir = f"content/references/{inf_config.handle.replace('@', '')}/"
    
    if not os.path.exists(reference_dir):
        raise HTTPException(
            status_code=400, 
            detail=f"No reference images found at {reference_dir}"
        )
    
    model_name = f"{inf_config.handle.replace('@', '')}-flux-lora"
    
    if not trigger_word:
        trigger_word = f"PHOTO_{inf_config.handle.replace('@', '').upper()}"
    
    try:
        result = await replicate_client.train_flux_lora(
            image_dir=reference_dir,
            model_name=model_name,
            trigger_word=trigger_word,
            training_steps=steps
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500, 
                detail=result.get("error", "Training failed")
            )
        
        if result.get("model_name"):
            TRAINED_MODELS[influencer.lower()] = {
                "model": result.get("model_name"),
                "trigger_word": trigger_word
            }
        
        return {
            "influencer": influencer,
            "reference_dir": reference_dir,
            "model_name": result.get("model_name"),
            "trigger_word": trigger_word,
            "training_id": result.get("training_id"),
            "status": result.get("status"),
            "message": "Training started! This will take 20-30 minutes. Use /training_status to check progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/training_status")
async def get_training_status(
    training_id: str = Query(..., description="Training ID to check")
):
    try:
        result = await replicate_client.get_training_status(training_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get training status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trainings")
async def list_trainings():
    try:
        trainings = await replicate_client.list_trainings()
        return {
            "count": len(trainings),
            "trainings": trainings
        }
    except Exception as e:
        logger.error(f"Failed to list trainings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


ALLOWED_LORA_MODELS = {
    "fastyfresh/luna_vale-flux-lora": "LUNAVALE",
    "fastyfresh/starbright_monroe-flux-lora": "STARBRIGHTMONROE",
}

@app.get("/generate_lora")
async def generate_with_lora(
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    prompt: str = Query(default="fashion editorial portrait", description="Generation prompt")
):
    logger.info(f"LoRA generation requested for {influencer}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    trained_info = TRAINED_MODELS.get(influencer.lower())
    if trained_info:
        model = trained_info["model"]
        trigger_word = trained_info["trigger_word"]
    else:
        model = None
        trigger_word = None
        for allowed_model, allowed_trigger in ALLOWED_LORA_MODELS.items():
            handle = inf_config.handle.replace('@', '')
            if handle in allowed_model:
                model = allowed_model
                trigger_word = allowed_trigger
                break
    
    if not model:
        raise HTTPException(
            status_code=400, 
            detail=f"No trained LoRA model found for {influencer}. Use /train to train one first."
        )
    
    output_dir = f"content/raw/{inf_config.handle.replace('@', '')}/"
    
    generation_params = {
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
                "long straight dark brown hair", "long silky straight hair", "perfectly straight hair", "straight hair not wavy",
                "dark brown eyes", "soft gentle expression",
                "realistic skin texture", "natural pores", "imperfect skin", "natural blemishes",
                "matte skin finish", "non-shiny skin", "photography studio lighting",
                "shot on Canon EOS R5 85mm f/1.4", "soft diffused daylight",
                "authentic candid moment", "real person photography", "photorealistic"
            ],
            "negative_prompt_additions": [
                "wavy hair", "curly hair", "messy hair", "frizzy hair", "volumized hair", "textured hair", "loose waves", "hair movement",
                "glossy skin", "shiny skin", "oily skin", "wet skin", "dewy skin", "poreless skin", "poreless",
                "airbrushed", "CGI", "plastic skin", "over-smooth", "smooth plastic face", "wax figure", "plastic figure",
                "uncanny", "diffusion artifacts", "overly perfect", "hyper smooth", "overly smoothed",
                "specular highlights on skin", "reflective skin", "glowing skin", "shine on face",
                "angular face", "sharp jawline", "chiseled features", "mature face", "harsh features",
                "heavy makeup", "intense expression", "serious expression", "angular cheekbones", "sculpted face"
            ]
        }
    }
    
    params = generation_params.get(inf_config.name, {})
    
    try:
        result = await replicate_client.generate_with_lora(
            prompt=prompt,
            model_name=model,
            trigger_word=trigger_word,
            output_dir=output_dir,
            filename_prefix=f"{inf_config.handle.replace('@', '')}_lora",
            generation_params=params
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "influencer": influencer,
            "model": model,
            "trigger_word": trigger_word,
            "prompt": prompt,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LoRA generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test_caption")
async def test_caption(
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    description: str = Query(default="morning yoga session on a sunny balcony", description="Content description")
):
    logger.info(f"Caption test for {influencer}: {description}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    identity_context = {
        "voice_tone": "bold and confident" if "fashion" in inf_config.niche.lower() else "warm and encouraging",
        "content_themes": ["style", "fashion", "beauty"] if "fashion" in inf_config.niche.lower() else ["wellness", "selfcare", "mindfulness"]
    }
    
    template_caption = content_service.generate_caption(inf_config, description, identity_context)
    
    try:
        llm_result = await content_service.generate_caption_async(inf_config, description, identity_context)
        
        return {
            "influencer": influencer,
            "description": description,
            "template_caption": template_caption,
            "llm_caption": llm_result.get("caption"),
            "llm_used": llm_result.get("llm_used", False),
            "source": llm_result.get("source"),
            "provider": llm_result.get("provider"),
            "latency_ms": llm_result.get("latency_ms"),
            "error": llm_result.get("llm_error")
        }
    except Exception as e:
        logger.error(f"Caption test failed: {e}")
        return {
            "influencer": influencer,
            "description": description,
            "template_caption": template_caption,
            "llm_caption": None,
            "llm_used": False,
            "error": str(e)
        }


@app.get("/llm_status")
async def llm_status():
    try:
        from app.tools.llm_client import LLMClient
        llm_client = LLMClient()
        return llm_client.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from app.agents.quality_agent import QualityAgent
quality_agent = QualityAgent()


@app.get("/quality_status")
async def quality_status():
    return quality_agent.get_status()


@app.get("/analyze_image")
async def analyze_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name")
):
    logger.info(f"Analyzing image: {image_path}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    current_params = {
        "lora_scale": 0.77,
        "guidance_scale": 2.5,
        "num_inference_steps": 30
    }
    
    result = await quality_agent.analyze_generation(
        image_path=image_path,
        influencer_name=inf_config.name,
        influencer_handle=inf_config.handle,
        prompt="",
        generation_params=current_params
    )
    
    return result.to_dict()


@app.get("/approve_image")
async def approve_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    approved: bool = Query(default=True, description="Approve or reject"),
    notes: Optional[str] = Query(default=None, description="Optional notes")
):
    logger.info(f"Recording feedback for {image_path}: approved={approved}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    current_params = {
        "lora_scale": 0.77,
        "guidance_scale": 2.5,
        "num_inference_steps": 30
    }
    
    profile = await quality_agent.record_feedback(
        influencer_name=inf_config.name,
        influencer_handle=inf_config.handle,
        image_path=image_path,
        prompt="",
        params=current_params,
        approved=approved,
        notes=notes
    )
    
    return {
        "status": "recorded",
        "image_path": image_path,
        "approved": approved,
        "profile_stats": {
            "total_generations": profile.total_generations,
            "approved_count": profile.approved_count,
            "approval_rate": f"{profile.approval_rate() * 100:.1f}%"
        }
    }


@app.get("/tuning_profile")
async def get_tuning_profile(
    influencer: str = Query(default="Luna Vale", description="Influencer name")
):
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    return quality_agent.get_profile_stats(inf_config.name, inf_config.handle)


@app.get("/gallery")
async def gallery_redirect():
    """Legacy gallery route - redirects to unified dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=301)


import json
import shutil

APPROVAL_STATUS_FILE = "data/approval_status.json"

def load_approval_status() -> dict:
    try:
        if os.path.exists(APPROVAL_STATUS_FILE):
            with open(APPROVAL_STATUS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load approval status: {e}")
    return {}

def save_approval_status(status: dict):
    try:
        os.makedirs(os.path.dirname(APPROVAL_STATUS_FILE), exist_ok=True)
        with open(APPROVAL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save approval status: {e}")


@app.get("/gallery/images/{influencer}")
async def get_gallery_images(influencer: str, source: str = Query(default="all")):
    """
    Get gallery images for an influencer.
    
    Args:
        influencer: Influencer ID (luna_vale, starbright_monroe)
        source: Filter by source - "all", "raw", "generated", "final", "research"
    """
    influencer_key = influencer.lower().replace(" ", "_")
    
    images = []
    
    if source in ["all", "generated"]:
        generated_folder = Path(f"content/generated/{influencer_key}")
        if generated_folder.exists():
            for file in generated_folder.glob("*.png"):
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "generated"
                })
    
    if source in ["all", "research"]:
        research_folder = Path("content/seedream4_output")
        if research_folder.exists():
            for file in research_folder.glob("research_*.png"):
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "research"
                })
    
    if source in ["all", "raw"]:
        raw_folder = Path(f"content/raw/{influencer_key}")
        if raw_folder.exists():
            for file in raw_folder.glob("*.png"):
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "raw"
                })
    
    if source in ["all", "final"]:
        final_folder = Path(f"content/final/{influencer_key}")
        if final_folder.exists():
            for file in final_folder.glob("*.png"):
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "final"
                })
    
    images.sort(key=lambda x: x["mtime"], reverse=True)
    
    for img in images:
        del img["mtime"]
    
    approval_status = load_approval_status()
    
    for img in images:
        if img["path"].startswith("content/final/"):
            approval_status[img["path"]] = "final"
    
    return {"images": images[:50], "approval_status": approval_status}


@app.get("/gallery/image/{path:path}")
async def serve_gallery_image(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    if not str(file_path).startswith("content/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        file_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.get("/gallery/download/{path:path}")
async def download_gallery_file(path: str):
    """Download a single image or video file."""
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not str(file_path).startswith("content/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    suffix = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )


@app.get("/gallery/download-all/{influencer}")
async def download_all_gallery_files(influencer: str, source: str = "all"):
    """Download all images and videos for an influencer as a ZIP file."""
    import zipfile
    import tempfile
    from datetime import datetime
    
    influencer_key = influencer.replace("@", "").lower().replace(" ", "_")
    
    files_to_zip = []
    
    folders = {
        "research": Path("content/seedream4_output"),
        "generated": Path(f"content/generated/{influencer_key}"),
        "raw": Path(f"content/raw/{influencer_key}"),
        "final": Path(f"content/final/{influencer_key}"),
        "loops": Path("content/loops"),
    }
    
    valid_extensions = {".png", ".jpg", ".jpeg", ".mp4", ".webm"}
    
    if source == "all":
        for folder_name, folder_path in folders.items():
            if folder_path.exists():
                for file in folder_path.iterdir():
                    if file.suffix.lower() in valid_extensions:
                        files_to_zip.append((file, folder_name))
    else:
        folder_path = folders.get(source)
        if folder_path and folder_path.exists():
            for file in folder_path.iterdir():
                if file.suffix.lower() in valid_extensions:
                    files_to_zip.append((file, source))
    
    if not files_to_zip:
        raise HTTPException(status_code=404, detail="No files found to download")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{influencer_key}_content_{timestamp}.zip"
    
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path, folder_name in files_to_zip:
            arcname = f"{folder_name}/{file_path.name}"
            zf.write(file_path, arcname)
    
    logger.info(f"Created ZIP with {len(files_to_zip)} files for {influencer}")
    
    return FileResponse(
        temp_zip.name,
        media_type="application/zip",
        filename=zip_filename,
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )


@app.get("/workflow/approve")
async def workflow_approve_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    auto_post: bool = Query(default=False, description="Auto-post to X after approval (Starbright only)")
):
    logger.info(f"Approving image: {image_path}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    source_path = Path(image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    handle = inf_config.handle.replace("@", "").lower()
    final_dir = Path(f"content/final/{handle}")
    final_dir.mkdir(parents=True, exist_ok=True)
    
    final_path = final_dir / source_path.name
    
    try:
        shutil.copy2(str(source_path), str(final_path))
        logger.info(f"Copied approved image to: {final_path}")
        
        approval_status = load_approval_status()
        approval_status[image_path] = "approved"
        approval_status[str(final_path)] = "final"
        save_approval_status(approval_status)
        
        current_params = {
            "lora_scale": 0.77,
            "guidance_scale": 2.5,
            "num_inference_steps": 30
        }
        
        await quality_agent.record_feedback(
            influencer_name=inf_config.name,
            influencer_handle=inf_config.handle,
            image_path=image_path,
            prompt="",
            params=current_params,
            approved=True,
            notes="Approved via gallery workflow"
        )
        
        twitter_result = None
        if auto_post and "starbright" in influencer.lower():
            twitter_result = await _auto_post_to_twitter(str(final_path), "starbright_monroe")
        
        return {
            "status": "approved",
            "image_path": image_path,
            "final_path": str(final_path),
            "influencer": influencer,
            "twitter_post": twitter_result
        }
        
    except Exception as e:
        logger.error(f"Failed to approve image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _auto_post_to_twitter(image_path: str, influencer_id: str = "starbright_monroe") -> dict:
    """
    Auto-generate caption, hashtags, CTA and post to Twitter/X
    """
    from app.agents.starbright_caption_generator import StarbrightCaptionGenerator
    from app.agents.twitter_oauth2_agent import TwitterOAuth2Agent
    
    try:
        caption_generator = StarbrightCaptionGenerator()
        twitter_agent = TwitterOAuth2Agent()
        
        logger.info(f"Auto-posting to X: {image_path}")
        
        caption_result = await caption_generator.generate_caption(
            hero_image_filename=Path(image_path).name
        )
        caption = caption_result.get("caption", "")
        
        if not caption:
            return {"error": "Failed to generate caption"}
        
        compose_result = await twitter_agent.compose_post(
            caption=caption,
            influencer=influencer_id,
            include_cta=True,
            include_hashtags=True,
            media_filename=Path(image_path).name,
            max_hashtags=5,
            use_dynamic_cta=True
        )
        
        full_text = compose_result.get("composed_text", caption)
        
        post_result = await twitter_agent.post_with_media(
            text=full_text,
            media_path=image_path,
            influencer=influencer_id
        )
        
        logger.info(f"Auto-post result: {post_result.get('status')}")
        
        return {
            "status": post_result.get("status"),
            "tweet_url": post_result.get("tweet_url"),
            "caption": caption,
            "full_text": full_text,
            "hashtags": compose_result.get("hashtags", []),
            "cta": compose_result.get("cta_used")
        }
        
    except Exception as e:
        logger.error(f"Auto-post to Twitter failed: {e}")
        return {"error": str(e)}


@app.post("/workflow/auto-post")
async def workflow_auto_post(
    image_path: str = Query(..., description="Path to approved image"),
    influencer: str = Query(default="starbright_monroe", description="Influencer ID")
):
    """
    Manually trigger auto-post for an already-approved image.
    Generates caption, hashtags, CTA and posts to X.
    """
    source_path = Path(image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    result = await _auto_post_to_twitter(str(source_path), influencer)
    
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@app.get("/workflow/reject")
async def workflow_reject_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    notes: Optional[str] = Query(default=None, description="Rejection reason")
):
    logger.info(f"Rejecting image: {image_path}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    approval_status = load_approval_status()
    approval_status[image_path] = "rejected"
    save_approval_status(approval_status)
    
    current_params = {
        "lora_scale": 0.77,
        "guidance_scale": 2.5,
        "num_inference_steps": 30
    }
    
    await quality_agent.record_feedback(
        influencer_name=inf_config.name,
        influencer_handle=inf_config.handle,
        image_path=image_path,
        prompt="",
        params=current_params,
        approved=False,
        notes=notes or "Rejected via gallery workflow"
    )
    
    archive_path = None
    try:
        source_path = Path(image_path)
        if source_path.exists():
            handle = inf_config.handle.replace("@", "").lower()
            archive_dir = Path(f"content/archives/{handle}")
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archive_file = archive_dir / source_path.name
            import shutil
            shutil.move(str(source_path), str(archive_file))
            archive_path = str(archive_file)
            logger.info(f"Archived rejected image to: {archive_path}")
            
            del approval_status[image_path]
            approval_status[archive_path] = "rejected"
            save_approval_status(approval_status)
    except Exception as e:
        logger.warning(f"Failed to archive rejected image: {e}")
    
    return {
        "status": "rejected",
        "image_path": image_path,
        "archive_path": archive_path,
        "influencer": influencer
    }


@app.delete("/content/delete")
async def delete_content(
    file_path: str = Query(..., description="Path to file to delete/archive"),
    content_type: str = Query(..., description="Type: raw, final, loop, captioned, hero_ref"),
    influencer: str = Query(default="luna_vale", description="Influencer handle")
):
    """Delete/archive any content type - moves to archives folder for recovery"""
    import shutil
    
    logger.info(f"Delete request: {file_path} (type: {content_type})")
    
    source_path = Path(file_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    handle = influencer.replace("@", "").lower()
    
    archive_subfolders = {
        "raw": "images",
        "final": "images", 
        "loop": "loops",
        "captioned": "captioned",
        "hero_ref": "hero_refs"
    }
    
    subfolder = archive_subfolders.get(content_type, "misc")
    archive_dir = Path(f"content/archives/{handle}/{subfolder}")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / source_path.name
    
    counter = 1
    while archive_file.exists():
        stem = source_path.stem
        suffix = source_path.suffix
        archive_file = archive_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    try:
        shutil.move(str(source_path), str(archive_file))
        logger.info(f"Archived {content_type} to: {archive_file}")
        
        return {
            "status": "deleted",
            "original_path": file_path,
            "archive_path": str(archive_file),
            "content_type": content_type,
            "influencer": influencer,
            "recoverable": True
        }
    except Exception as e:
        logger.error(f"Failed to archive content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@app.get("/archives/list")
async def list_archived_content(
    influencer: str = Query(default="luna_vale", description="Influencer handle"),
    content_type: Optional[str] = Query(default=None, description="Filter by type: images, loops, captioned, hero_refs")
):
    """List all archived content for an influencer"""
    handle = influencer.replace("@", "").lower()
    archive_base = Path(f"content/archives/{handle}")
    
    if not archive_base.exists():
        return {"influencer": influencer, "archives": {}, "total": 0}
    
    archives = {}
    total = 0
    
    subfolders = ["images", "loops", "captioned", "hero_refs"]
    if content_type:
        subfolders = [content_type]
    
    for subfolder in subfolders:
        folder = archive_base / subfolder
        if folder.exists():
            files = []
            for f in folder.iterdir():
                if f.is_file():
                    files.append({
                        "filename": f.name,
                        "path": str(f),
                        "size_kb": f.stat().st_size / 1024,
                        "archived_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
                    total += 1
            if files:
                files.sort(key=lambda x: x["archived_at"], reverse=True)
                archives[subfolder] = files
    
    return {
        "influencer": influencer,
        "archives": archives,
        "total": total
    }


@app.post("/archives/restore")
async def restore_from_archive(
    archive_path: str = Query(..., description="Path to archived file"),
    content_type: str = Query(..., description="Type: images, loops, captioned, hero_refs"),
    influencer: str = Query(default="luna_vale", description="Influencer handle")
):
    """Restore a file from archives back to its original location"""
    import shutil
    
    source_path = Path(archive_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Archived file not found: {archive_path}")
    
    handle = influencer.replace("@", "").lower()
    
    restore_paths = {
        "images": f"content/raw/{handle}",
        "loops": f"content/loops/{handle}",
        "captioned": "content/loops/captioned",
        "hero_refs": f"content/references/{handle}/hero"
    }
    
    dest_dir = Path(restore_paths.get(content_type, f"content/raw/{handle}"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_file = dest_dir / source_path.name
    
    try:
        shutil.move(str(source_path), str(dest_file))
        logger.info(f"Restored from archive: {dest_file}")
        
        return {
            "status": "restored",
            "archive_path": archive_path,
            "restored_path": str(dest_file),
            "content_type": content_type,
            "influencer": influencer
        }
    except Exception as e:
        logger.error(f"Failed to restore from archive: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore: {str(e)}")


@app.get("/workflow/stats")
async def workflow_stats(
    influencer: str = Query(default="Luna Vale", description="Influencer name")
):
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    handle = inf_config.handle.replace("@", "").lower()
    
    raw_dir = Path(f"content/raw/{handle}")
    final_dir = Path(f"content/final/{handle}")
    
    raw_count = len(list(raw_dir.glob("*.png"))) if raw_dir.exists() else 0
    final_count = len(list(final_dir.glob("*.png"))) if final_dir.exists() else 0
    
    approval_status = load_approval_status()
    approved_count = sum(1 for v in approval_status.values() if v in ["approved", "final"])
    rejected_count = sum(1 for v in approval_status.values() if v == "rejected")
    pending_count = raw_count - approved_count - rejected_count
    
    return {
        "influencer": influencer,
        "raw_images": raw_count,
        "final_images": final_count,
        "approved": approved_count,
        "rejected": rejected_count,
        "pending": max(0, pending_count),
        "approval_rate": f"{(approved_count / raw_count * 100):.1f}%" if raw_count > 0 else "N/A"
    }


from app.agents.face_swap_agent import FaceSwapAgent
face_swap_agent = FaceSwapAgent()


@app.get("/face_swap")
async def face_swap_image(
    image_path: str = Query(..., description="Path to target image to swap face onto"),
    influencer: str = Query(default="Starbright Monroe", description="Influencer name (determines source face)")
):
    logger.info(f"Face swap requested: {image_path} -> {influencer}")
    
    result = await face_swap_agent.swap_face(
        target_image_path=image_path,
        influencer_name=influencer
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {
        "status": "success",
        "original_image": image_path,
        "influencer": influencer,
        "swapped_image": result.get("image_path"),
        "model_used": result.get("model")
    }


@app.post("/face_swap")
async def face_swap_image_post(
    image_path: str = Query(..., description="Path to target image"),
    influencer: str = Query(default="Starbright Monroe", description="Influencer name")
):
    return await face_swap_image(image_path=image_path, influencer=influencer)


@app.get("/bodies")
async def list_body_images():
    """List all body images available for face swapping."""
    bodies_dir = "content/bodies"
    swapped_dir = "content/face_swapped"
    
    bodies = []
    if os.path.exists(bodies_dir):
        for filename in sorted(os.listdir(bodies_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                path = os.path.join(bodies_dir, filename)
                bodies.append({
                    "filename": filename,
                    "path": path
                })
    
    swapped = []
    if os.path.exists(swapped_dir):
        for filename in sorted(os.listdir(swapped_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                path = os.path.join(swapped_dir, filename)
                swapped.append({
                    "filename": filename,
                    "path": path
                })
    
    return {
        "bodies": bodies,
        "swapped": swapped,
        "bodies_count": len(bodies),
        "swapped_count": len(swapped)
    }


class BatchFaceSwapRequest(BaseModel):
    image_paths: list[str]
    influencer: str = "Starbright Monroe"
    mode: str = "simple"


@app.post("/face_swap/batch")
async def batch_face_swap(request: BatchFaceSwapRequest):
    """Batch face swap on multiple body images."""
    results = []
    
    for image_path in request.image_paths:
        try:
            result = await face_swap_agent.swap_face(
                target_image_path=image_path,
                influencer_name=request.influencer
            )
            results.append({
                "original": image_path,
                "status": result.get("status", "error"),
                "swapped_path": result.get("image_path"),
                "error": result.get("error")
            })
        except Exception as e:
            results.append({
                "original": image_path,
                "status": "error",
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r["status"] == "success")
    
    return {
        "total": len(request.image_paths),
        "success": success_count,
        "failed": len(request.image_paths) - success_count,
        "results": results
    }


@app.post("/bodies/upload")
async def upload_body_image(file: UploadFile = File(...)):
    """Upload a body image for face swapping."""
    bodies_dir = "content/bodies"
    os.makedirs(bodies_dir, exist_ok=True)
    
    filename = file.filename
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(status_code=400, detail="Only image files allowed")
    
    file_path = os.path.join(bodies_dir, filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "status": "success",
        "filename": filename,
        "path": file_path
    }


@app.get("/canonical_faces")
async def list_canonical_faces():
    faces = {}
    for inf in INFLUENCERS:
        if inf.canonical_face_path and os.path.exists(inf.canonical_face_path):
            faces[inf.name] = {
                "path": inf.canonical_face_path,
                "exists": True,
                "lora_model": inf.lora_model,
                "lora_trigger_word": inf.lora_trigger_word
            }
        else:
            faces[inf.name] = {
                "path": inf.canonical_face_path,
                "exists": False,
                "lora_model": inf.lora_model,
                "lora_trigger_word": inf.lora_trigger_word
            }
    return {"canonical_faces": faces}


from app.pipeline_orchestrator import PipelineOrchestrator

pipeline_orchestrator = PipelineOrchestrator()
manual_queue_agent = pipeline_orchestrator.manual_queue


class PipelineRequest(BaseModel):
    influencer: Optional[str] = None
    dry_run: bool = False
    skip_generation: bool = False
    skip_posting: bool = False


@app.post("/pipeline/run")
async def run_pipeline(request: PipelineRequest = None):
    """Run the full daily automation pipeline"""
    if request is None:
        request = PipelineRequest()
    
    logger.info(f"Pipeline run requested: dry_run={request.dry_run}, skip_generation={request.skip_generation}")
    
    influencer = None
    if request.influencer:
        for inf in INFLUENCERS:
            if inf.name.lower() == request.influencer.lower():
                influencer = inf
                break
        if not influencer:
            raise HTTPException(status_code=404, detail=f"Influencer not found: {request.influencer}")
    
    try:
        result = await pipeline_orchestrator.run_daily_pipeline(
            influencer=influencer,
            dry_run=request.dry_run,
            skip_generation=request.skip_generation,
            skip_posting=request.skip_posting
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get pipeline configuration and status"""
    return await pipeline_orchestrator.get_pipeline_status()


@app.get("/pipeline/dry_run")
async def pipeline_dry_run(
    influencer: Optional[str] = Query(default=None, description="Optional influencer name")
):
    """Run pipeline in dry run mode (no actual posts)"""
    request = PipelineRequest(
        influencer=influencer,
        dry_run=True,
        skip_generation=False,
        skip_posting=False
    )
    return await run_pipeline(request)


@app.get("/manual_queue")
async def get_manual_queue(
    platform: Optional[str] = Query(default=None, description="Filter by platform (instagram_manual, tiktok_manual)"),
    influencer: Optional[str] = Query(default=None, description="Filter by influencer handle"),
    status: Optional[str] = Query(default="pending", description="Filter by status (pending, posted)")
):
    """Get manual posting queue for IG/TikTok"""
    items = await manual_queue_agent.get_queue(
        platform=platform,
        influencer_handle=influencer,
        status=status
    )
    return {
        "items": [item.model_dump() for item in items],
        "count": len(items)
    }


@app.post("/manual_queue/mark_posted")
async def mark_queue_item_posted(
    item_id: str = Query(..., description="Queue item ID to mark as posted"),
    notes: Optional[str] = Query(default=None, description="Optional notes")
):
    """Mark a manual queue item as posted"""
    result = await manual_queue_agent.mark_as_posted(item_id, notes)
    if result:
        return {"status": "success", "item": result.model_dump()}
    raise HTTPException(status_code=404, detail=f"Queue item not found: {item_id}")


@app.get("/manual_queue/stats")
async def get_manual_queue_stats(
    influencer: Optional[str] = Query(default=None, description="Filter by influencer handle")
):
    """Get manual queue statistics"""
    return await manual_queue_agent.get_queue_stats(influencer_handle=influencer)



@app.get("/influencer/workflow_type")
async def get_influencer_workflow_type(
    influencer: str = Query(..., description="Influencer handle")
):
    """Get the workflow type for an influencer (lora_full or micro_loop)"""
    handle = influencer.replace("@", "").lower()
    
    for inf in INFLUENCERS:
        inf_handle = inf.handle.replace("@", "").lower()
        if inf_handle == handle:
            return {
                "influencer": inf.name,
                "handle": inf.handle,
                "workflow_type": inf.workflow_type,
                "hero_refs": inf.hero_refs if inf.workflow_type == "micro_loop" else []
            }
    
    raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")


# Music Library Endpoints
from app.agents.music_optimization_agent import music_agent, merge_audio_video

@app.get("/api/music/tracks")
async def list_music_tracks(
    mood: Optional[str] = Query(None, description="Filter by mood"),
    genre: Optional[str] = Query(None, description="Filter by genre")
):
    """List available music tracks"""
    tracks = music_agent.list_tracks(mood=mood, genre=genre)
    return {
        "tracks": tracks,
        "count": len(tracks),
        "categories": music_agent.metadata.get("categories", {})
    }

def _detect_music_attributes(filename: str) -> dict:
    """Auto-detect mood, tempo, and genre from filename keywords"""
    name_lower = filename.lower()
    
    mood_keywords = {
        "chill": ["chill", "relax", "calm", "peaceful", "mellow", "soft", "cozy", "lofi", "lo-fi"],
        "upbeat": ["upbeat", "happy", "fun", "bright", "cheerful", "positive", "joyful"],
        "sensual": ["sensual", "sexy", "seductive", "sultry", "intimate", "hot", "desire"],
        "dreamy": ["dreamy", "dream", "ethereal", "floating", "ambient", "atmospheric"],
        "energetic": ["energetic", "energy", "hype", "intense", "power", "dynamic", "edm"],
        "romantic": ["romantic", "love", "heart", "sweet", "tender", "passionate"],
        "mysterious": ["mysterious", "dark", "moody", "tension", "suspense", "cinematic"]
    }
    
    tempo_keywords = {
        "slow": ["slow", "ballad", "ambient", "peaceful", "calm"],
        "fast": ["fast", "upbeat", "energetic", "hype", "edm", "dance"],
        "medium": ["medium", "moderate", "chill", "groove"]
    }
    
    genre_keywords = {
        "lofi": ["lofi", "lo-fi", "chill", "beats", "hip-hop"],
        "pop": ["pop", "catchy", "mainstream"],
        "rnb": ["rnb", "r&b", "soul", "smooth"],
        "electronic": ["electronic", "edm", "synth", "techno", "house"],
        "ambient": ["ambient", "atmospheric", "soundscape"],
        "acoustic": ["acoustic", "guitar", "piano", "unplugged"],
        "tropical": ["tropical", "summer", "beach", "island"]
    }
    
    detected_mood = "chill"
    detected_tempo = "medium"
    detected_genre = "lofi"
    
    for mood, keywords in mood_keywords.items():
        if any(kw in name_lower for kw in keywords):
            detected_mood = mood
            break
    
    for tempo, keywords in tempo_keywords.items():
        if any(kw in name_lower for kw in keywords):
            detected_tempo = tempo
            break
    
    for genre, keywords in genre_keywords.items():
        if any(kw in name_lower for kw in keywords):
            detected_genre = genre
            break
    
    return {"mood": detected_mood, "tempo": detected_tempo, "genre": detected_genre}

@app.post("/api/music/upload")
async def upload_music_track(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Track title (auto-detected from filename if not provided)"),
    mood: Optional[str] = Query(None, description="Track mood (auto-detected from filename if not provided)"),
    tempo: Optional[str] = Query(None, description="Track tempo (auto-detected from filename if not provided)"),
    genre: Optional[str] = Query(None, description="Track genre (auto-detected from filename if not provided)"),
    artist: str = Query("Unknown", description="Artist name")
):
    """Upload a new music track to the library with auto-detection of mood/genre from filename"""
    music_dir = Path("content/music/library")
    music_dir.mkdir(parents=True, exist_ok=True)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    original_filename = file.filename
    filename = original_filename.replace(" ", "_").lower()
    file_path = music_dir / filename
    
    detected = _detect_music_attributes(original_filename)
    final_mood = mood or detected["mood"]
    final_tempo = tempo or detected["tempo"]
    final_genre = genre or detected["genre"]
    final_title = title or original_filename.replace("_", " ").rsplit(".", 1)[0]
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(file_path)]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        duration = int(float(json.loads(result.stdout)["format"]["duration"]))
    except:
        duration = 10
    
    track = music_agent.add_track(
        filename=filename,
        title=final_title,
        mood=final_mood,
        tempo=final_tempo,
        genre=final_genre,
        duration_seconds=duration,
        artist=artist
    )
    
    logging.info(f"Uploaded music track: {filename} - mood={final_mood}, tempo={final_tempo}, genre={final_genre}")
    return {"success": True, "track": track, "detected": detected}

@app.post("/api/telegram/upload-content")
async def upload_telegram_content(
    file: UploadFile = File(...),
    persona: str = Query("starbright_monroe", description="Persona: starbright_monroe or luna_vale"),
    content_type: str = Query("videos", description="Content type: videos, welcome_pack, teaser, or photos")
):
    """Upload video/photo content for Telegram bots"""
    persona_folder = "starbright" if persona == "starbright_monroe" else "luna"
    upload_dir = Path(f"content/telegram/{persona_folder}/{content_type}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    filename = file.filename.replace(" ", "_")
    file_path = upload_dir / filename
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    logging.info(f"Uploaded Telegram content: {file_path}")
    return {
        "success": True, 
        "path": str(file_path),
        "filename": filename,
        "persona": persona,
        "content_type": content_type
    }

@app.get("/api/telegram/content")
async def list_telegram_content(
    persona: str = Query("starbright_monroe", description="Persona"),
    content_type: str = Query("videos", description="Content type")
):
    """List uploaded Telegram content"""
    persona_folder = "starbright" if persona == "starbright_monroe" else "luna"
    content_dir = Path(f"content/telegram/{persona_folder}/{content_type}")
    
    if not content_dir.exists():
        return {"files": []}
    
    files = []
    for f in content_dir.iterdir():
        if f.is_file():
            files.append({
                "filename": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1)
            })
    
    return {"files": sorted(files, key=lambda x: x["filename"])}

@app.get("/api/music/trends")
async def analyze_music_trends():
    """Analyze current audio trends on X for optimization"""
    result = await music_agent.analyze_x_audio_trends()
    return result

@app.get("/api/music/recommend")
async def recommend_music(
    video_filename: str = Query(..., description="Video filename to match music to"),
    influencer: str = Query("starbright_monroe", description="Influencer"),
    caption: Optional[str] = Query(None, description="Caption text to analyze for mood matching")
):
    """Get AI-powered music recommendation based on caption mood"""
    result = await music_agent.recommend_music_for_caption(caption, video_filename, influencer)
    return result

@app.post("/api/music/merge")
async def merge_music_with_video(
    video_path: str = Query(..., description="Path to the video file"),
    track_id: str = Query(..., description="Track ID from library"),
    audio_volume: float = Query(0.3, description="Audio volume (0.0-1.0)"),
    influencer: str = Query("starbright_monroe", description="Influencer")
):
    """Merge a music track with a video file"""
    track_path = music_agent.get_track_path(track_id)
    if not track_path:
        raise HTTPException(status_code=404, detail=f"Track not found: {track_id}")
    
    if not Path(video_path).exists():
        raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")
    
    output_dir = Path("content/loops/with_music")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_filename = Path(video_path).stem
    output_filename = f"{video_filename}_music.mp4"
    output_path = output_dir / output_filename
    
    result = merge_audio_video(
        video_path=video_path,
        audio_path=str(track_path),
        output_path=str(output_path),
        audio_volume=audio_volume
    )
    
    if result.get("success"):
        return {
            "success": True,
            "output_path": str(output_path),
            "filename": output_filename,
            "video_duration": result.get("video_duration")
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Merge failed"))

@app.get("/api/music/file/{filename:path}")
async def serve_music_file(filename: str):
    """Serve a music file"""
    file_path = Path("content/music/library") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Music file not found")
    return FileResponse(str(file_path), media_type="audio/mpeg")


from app.agents.twitter_oauth2_agent import TwitterOAuth2Agent
twitter_oauth2_agent = TwitterOAuth2Agent()


@app.get("/api/twitter/status")
async def twitter_status():
    """Get Twitter OAuth 2.0 connection status"""
    return twitter_oauth2_agent.get_status()


@app.get("/api/twitter/auth")
async def twitter_auth():
    """Start Twitter OAuth 2.0 authorization flow"""
    result = twitter_oauth2_agent.get_authorization_url()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter Authorization</title>
        <style>
            body {{ font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }}
            a {{ color: #1da1f2; font-size: 18px; }}
            .box {{ background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            code {{ background: #0f0f23; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>🐦 Twitter Authorization</h1>
        <div class="box">
            <p>Click the button below to authorize this app to post on your behalf:</p>
            <p><a href="{result['auth_url']}" target="_blank">➡️ Authorize with Twitter</a></p>
        </div>
        <div class="box">
            <p><strong>After authorizing:</strong></p>
            <p>You'll be redirected to a callback URL. The authorization will complete automatically.</p>
        </div>
    </body>
    </html>
    """)


@app.get("/api/twitter/callback")
async def twitter_callback(request: Request):
    """Handle Twitter OAuth 2.0 callback"""
    callback_url = str(request.url)
    
    result = twitter_oauth2_agent.handle_callback(callback_url)
    
    if "error" in result:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Failed</title>
            <style>
                body {{ font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }}
                .error {{ background: #4a1515; padding: 20px; border-radius: 10px; border: 1px solid #ff4444; }}
            </style>
        </head>
        <body>
            <h1>❌ Authorization Failed</h1>
            <div class="error">
                <p>{result['error']}</p>
                <p><a href="/api/twitter/auth" style="color: #1da1f2;">Try again</a></p>
            </div>
        </body>
        </html>
        """)
    
    user = result.get("user", {})
    username = user.get("username", "Unknown")
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authorization Successful!</title>
        <style>
            body {{ font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }}
            .success {{ background: #1a4a1a; padding: 20px; border-radius: 10px; border: 1px solid #44ff44; }}
            a {{ color: #1da1f2; }}
        </style>
    </head>
    <body>
        <h1>✅ Authorization Successful!</h1>
        <div class="success">
            <p>Connected as: <strong>@{username}</strong></p>
            <p>The app can now post tweets on your behalf.</p>
            <p><a href="/api/twitter/test">Test posting</a> | <a href="/dashboard">Back to Dashboard</a></p>
        </div>
    </body>
    </html>
    """)


@app.get("/api/twitter/test")
async def twitter_test_post():
    """Test Twitter posting with a simple tweet"""
    result = await twitter_oauth2_agent.post_text("🤖 Test post from AIA Engine! #AIInfluencer")
    return result


@app.post("/api/twitter/post")
async def twitter_post(
    text: str = Query(..., description="Tweet text"),
    media_path: Optional[str] = Query(default=None, description="Optional media path")
):
    """Post to Twitter"""
    if media_path:
        result = await twitter_oauth2_agent.post_with_media(text, media_path)
    else:
        result = await twitter_oauth2_agent.post_text(text)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.post("/api/twitter/post_full")
async def twitter_post_full(
    caption: str = Query(..., description="Main caption text"),
    media_path: str = Query(..., description="Path to video/image file"),
    influencer: str = Query(default="starbright_monroe", description="Influencer name"),
    include_cta: bool = Query(default=True, description="Include Fanvue CTA"),
    include_hashtags: bool = Query(default=True, description="Include hashtags"),
    include_music: bool = Query(default=False, description="Include background music"),
    music_track_id: Optional[str] = Query(default=None, description="Music track ID to merge")
):
    """
    Post a complete package to Twitter: video + caption + CTA + hashtags
    This is the main endpoint for automated posting.
    Optionally merges background music before posting.
    """
    final_media_path = media_path
    
    if include_music and music_track_id:
        track_path = music_agent.get_track_path(music_track_id)
        if track_path and Path(media_path).exists():
            output_dir = Path("content/loops/with_music")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            video_filename = Path(media_path).stem
            output_filename = f"{video_filename}_music.mp4"
            output_path = output_dir / output_filename
            
            logger.info(f"Merging music track {music_track_id} with video {media_path}")
            merge_result = merge_audio_video(
                video_path=media_path,
                audio_path=str(track_path),
                output_path=str(output_path),
                audio_volume=0.3
            )
            
            if merge_result.get("success"):
                final_media_path = str(output_path)
                logger.info(f"Music merged successfully: {final_media_path}")
            else:
                logger.warning(f"Music merge failed: {merge_result.get('error')}")
    
    result = await twitter_oauth2_agent.post_full_package(
        caption=caption,
        media_path=final_media_path,
        influencer=influencer,
        include_cta=include_cta,
        include_hashtags=include_hashtags
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    result["music_added"] = include_music and music_track_id is not None
    return result


@app.get("/api/twitter/compose")
async def twitter_compose_preview(
    caption: str = Query(..., description="Main caption text"),
    influencer: str = Query(default="starbright_monroe", description="Influencer name"),
    include_cta: bool = Query(default=True, description="Include Fanvue CTA"),
    include_hashtags: bool = Query(default=True, description="Include hashtags"),
    media_filename: str = Query(default=None, description="Media filename for context-aware hashtags")
):
    """Preview composed tweet text with dynamic AI-optimized hashtags"""
    result = await twitter_oauth2_agent.compose_post(
        caption=caption,
        influencer=influencer,
        include_cta=include_cta,
        include_hashtags=include_hashtags,
        media_filename=media_filename,
        max_hashtags=5
    )
    return result


@app.get("/api/twitter/disconnect")
async def twitter_disconnect():
    """Disconnect Twitter authorization"""
    return twitter_oauth2_agent.disconnect()


from app.agents.fanvue_cta_optimizer import FanvueCTAOptimizer, get_optimizer

@app.get("/api/cta/optimize")
async def cta_optimize_all(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Get all CTA optimization suggestions: bio, pinned post, CTA templates"""
    optimizer = get_optimizer(persona)
    result = await optimizer.optimize_all()
    return result


@app.get("/api/cta/bio")
async def cta_generate_bio(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Generate AI-optimized bio suggestion"""
    optimizer = get_optimizer(persona)
    result = await optimizer.generate_bio_suggestion()
    return result


@app.get("/api/cta/pinned")
async def cta_generate_pinned(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Generate AI-optimized pinned post content"""
    optimizer = get_optimizer(persona)
    result = await optimizer.generate_pinned_post()
    return result


@app.get("/api/cta/post")
async def cta_generate_post_cta(
    persona: str = Query(default="starbright_monroe", description="Persona name"),
    content_type: str = Query(default="photo", description="Content type (photo/video)"),
    setting: str = Query(default="casual", description="Content setting/context")
):
    """Generate context-aware CTA for a specific post"""
    optimizer = get_optimizer(persona)
    cta = await optimizer.generate_post_cta({
        "content_type": content_type,
        "setting": setting
    })
    return {"cta": cta}


@app.get("/api/cta/library")
async def cta_get_library(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Get full CTA template library"""
    optimizer = get_optimizer(persona)
    return {
        "templates": optimizer.get_cta_library(),
        "persona": persona
    }


@app.get("/api/cta/random")
async def cta_get_random(
    persona: str = Query(default="starbright_monroe", description="Persona name"),
    category: str = Query(default=None, description="CTA category (soft_tease, curiosity, direct, exclusive)")
):
    """Get a random CTA from the library"""
    optimizer = get_optimizer(persona)
    return {"cta": optimizer.get_random_cta(category)}


from app.agents.content_calendar_agent import get_calendar_agent
from app.services.seedream4_service import Seedream4Service

seedream4_service = Seedream4Service()


class Seedream4GenerateRequest(BaseModel):
    prompt: str
    scene: str = ""
    outfit: str = ""
    pose: str = "natural relaxed pose"
    aspect_ratio: str = "9:16"
    seed: Optional[int] = None
    filename_prefix: str = "starbright"


@app.post("/api/seedream4/generate")
async def seedream4_generate(request: Seedream4GenerateRequest):
    """Generate image using Seedream4 with face + body reference images"""
    
    if request.prompt:
        prompt = request.prompt
    else:
        prompt = seedream4_service.build_prompt(
            scene=request.scene,
            outfit=request.outfit,
            pose=request.pose
        )
    
    result = await seedream4_service.generate(
        prompt=prompt,
        aspect_ratio=request.aspect_ratio,
        seed=request.seed,
        filename_prefix=request.filename_prefix
    )
    
    return result


@app.get("/api/seedream4/generate-quick")
async def seedream4_generate_quick(
    scene: str = Query(default="minimalist modern luxury apartment", description="Scene/setting"),
    outfit: str = Query(default="pink two-piece bikini", description="Outfit description"),
    lighting: str = Query(default="evening interior lighting, warm ambient light", description="Lighting"),
    seed: int = Query(default=None, description="Random seed")
):
    """Quick generate with V3 prompt format (pale ivory skin, slim athletic build)"""
    
    prompt = seedream4_service.build_prompt_simple(
        outfit=outfit,
        scene=scene,
        lighting=lighting
    )
    
    result = await seedream4_service.generate(
        prompt=prompt,
        seed=seed,
        filename_prefix="quick"
    )
    
    return result


class ContentGenerateRequest(BaseModel):
    outfit: str
    scene: str
    lighting: str = "natural lighting"
    accessories: str = "random"
    filename_prefix: str = "starbright"
    count: int = 1


@app.post("/api/seedream4/content")
async def seedream4_generate_content(request: ContentGenerateRequest):
    """
    Generate content at scale using optimized V3 prompt format
    
    Accessories options:
    - "none": No jewelry/earrings
    - "minimal": Small stud earrings only
    - "earrings": Small hoop earrings
    - "necklace": Delicate necklace, no earrings
    - "random": Randomly varies accessories (default, weighted toward no earrings)
    """
    from app.services.seedream4_service import Seedream4Service
    
    service = Seedream4Service()
    results = []
    
    for i in range(request.count):
        prefix = f"{request.filename_prefix}_{i+1}" if request.count > 1 else request.filename_prefix
        result = await service.generate_content(
            outfit=request.outfit,
            scene=request.scene,
            lighting=request.lighting,
            accessories=request.accessories,
            filename_prefix=prefix
        )
        results.append(result)
    
    return {
        "status": "success",
        "count": len(results),
        "results": results
    }


@app.get("/api/seedream4/presets")
async def seedream4_get_presets():
    """Get available content presets for quick generation"""
    from app.services.seedream4_service import CONTENT_PRESETS
    return {"presets": CONTENT_PRESETS}


@app.get("/api/seedream4/images")
async def seedream4_list_images(limit: int = Query(default=20)):
    """List generated Seedream4 images"""
    output_dir = Path("content/seedream4_output")
    if not output_dir.exists():
        return {"images": [], "count": 0}
    
    images = []
    for f in sorted(output_dir.glob("*.png"), reverse=True)[:limit]:
        images.append({
            "filename": f.name,
            "path": str(f),
            "url": f"/content/seedream4_output/{f.name}",
            "size_kb": round(f.stat().st_size / 1024, 1),
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return {"images": images, "count": len(images)}


@app.post("/api/seedream4/face-swap")
async def seedream4_face_swap(
    image_path: str = Query(..., description="Path to generated Seedream4 image")
):
    """Face swap a Seedream4 generated image with Starbright canonical face"""
    from app.agents.face_swap_agent import FaceSwapAgent
    
    swap_agent = FaceSwapAgent()
    
    result = await swap_agent.swap_face(
        target_image_path=image_path,
        influencer_name="Starbright Monroe",
        output_dir="content/seedream4_swapped"
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {
        "status": "success",
        "original": image_path,
        "swapped": result.get("image_path")
    }






from app.agents.unified_content_agent import unified_content_agent, INFLUENCER_CONFIG

class UnifiedGenerateRequest(BaseModel):
    influencer_id: str = "starbright_monroe"
    theme: str = "general"
    outfit: str = "casual outfit"
    time_of_day: Optional[str] = None
    use_background_ref: bool = True
    filename: Optional[str] = None

class UnifiedWeeklyRequest(BaseModel):
    influencer_id: str = "starbright_monroe"
    content_plan: list[dict]
    use_background_ref: bool = True

@app.get("/api/unified/influencers")
async def unified_list_influencers():
    """List available influencers for unified content generation"""
    influencers = []
    for inf_id, config in INFLUENCER_CONFIG.items():
        influencers.append({
            "id": inf_id,
            "name": config["name"],
            "face_ref": config["face_ref"],
            "body_ref": config["body_ref"],
            "output_dir": config["output_dir"]
        })
    return {"influencers": influencers}

@app.post("/api/unified/generate")
async def unified_generate_content(request: UnifiedGenerateRequest):
    """
    Generate a single piece of content using the Unified Content Agent.
    
    Uses Seedream4 with dual-reference (face + body) and optional background reference.
    Includes LLM-powered pose/expression selection and theme-appropriate backgrounds.
    """
    if request.influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown influencer: {request.influencer_id}. Available: {list(INFLUENCER_CONFIG.keys())}"
        )
    
    try:
        result = await unified_content_agent.generate_content(
            influencer_id=request.influencer_id,
            theme=request.theme,
            outfit=request.outfit,
            time_of_day=request.time_of_day,
            use_background_ref=request.use_background_ref,
            filename=request.filename
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/unified/generate-weekly")
async def unified_generate_weekly(request: UnifiedWeeklyRequest):
    """
    Generate a full week of content for a specific influencer.
    
    Content plan should be a list of dicts with: theme, outfit, time_of_day, filename
    """
    if request.influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown influencer: {request.influencer_id}. Available: {list(INFLUENCER_CONFIG.keys())}"
        )
    
    try:
        results = await unified_content_agent.generate_weekly_content(
            influencer_id=request.influencer_id,
            content_plan=request.content_plan,
            use_background_ref=request.use_background_ref
        )
        successful = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": len(results) - successful
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified weekly generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/unified/generated")
async def unified_list_generated(
    influencer_id: str = Query(default="starbright_monroe"),
    limit: int = Query(default=50)
):
    """List generated images from unified content agent"""
    try:
        config = INFLUENCER_CONFIG.get(influencer_id)
        if not config:
            return {"error": f"Unknown influencer: {influencer_id}"}
        
        output_dir = Path(config["output_dir"])
        if not output_dir.exists():
            return {"influencer": influencer_id, "images": [], "count": 0}
        
        images = []
        for img_path in sorted(output_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            images.append({
                "filename": img_path.name,
                "path": str(img_path),
                "url": f"/api/unified/image/{influencer_id}/{img_path.name}",
                "size_kb": img_path.stat().st_size // 1024,
                "created": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat()
            })
        
        return {"influencer": influencer_id, "images": images, "count": len(images)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/unified/image/{influencer_id}/{filename}")
async def unified_serve_image(influencer_id: str, filename: str):
    """Serve a generated image from unified content agent"""
    config = INFLUENCER_CONFIG.get(influencer_id)
    if not config:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    image_path = Path(config["output_dir"]) / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path, media_type="image/png")


from app.agents.dataset_quality_agent import DatasetQualityAgent
dataset_quality_agent = DatasetQualityAgent()

class ScoreImageRequest(BaseModel):
    image_path: str

class CurationActionRequest(BaseModel):
    image_path: str
    delete: bool = False

@app.get("/api/curation/stats")
async def curation_stats(persona: str = Query(default="starbright")):
    """Get curation statistics for a persona"""
    stats = dataset_quality_agent.get_curation_stats(persona)
    return stats

@app.get("/api/curation/pending")
async def curation_pending(persona: str = Query(default="starbright")):
    """Get list of images pending quality review"""
    pending = dataset_quality_agent.get_pending_images(persona)
    return {"persona": persona, "pending": pending, "count": len(pending)}

@app.post("/api/curation/score")
async def curation_score_image(request: ScoreImageRequest):
    """Score a single image against reference images"""
    result = await dataset_quality_agent.score_image(request.image_path)
    
    score_file = request.image_path.replace(".png", "_score.json").replace(".jpg", "_score.json")
    try:
        with open(score_file, "w") as f:
            json.dump({
                "score": result.score,
                "recommendation": result.recommendation,
                "face_match": result.face_match,
                "hair_match": result.hair_match,
                "body_match": result.body_match,
                "overall_identity": result.overall_identity,
                "issues": result.issues,
                "notes": result.notes,
                "status": "pending"
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save score file: {e}")
    
    return result

@app.post("/api/curation/score-batch")
async def curation_score_batch(
    persona: str = Query(default="starbright"),
    limit: int = Query(default=10, description="Max images to score in one batch")
):
    """Score multiple pending images"""
    pending = dataset_quality_agent.get_pending_images(persona)[:limit]
    results = {}
    
    for image_path in pending:
        result = await dataset_quality_agent.score_image(image_path)
        results[image_path] = {
            "score": result.score,
            "recommendation": result.recommendation,
            "face_match": result.face_match,
            "hair_match": result.hair_match,
            "body_match": result.body_match,
            "issues": result.issues,
            "notes": result.notes
        }
        
        score_file = image_path.replace(".png", "_score.json").replace(".jpg", "_score.json")
        try:
            with open(score_file, "w") as f:
                json.dump({
                    **results[image_path],
                    "overall_identity": result.overall_identity,
                    "status": "pending"
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save score file: {e}")
    
    return {"scored": len(results), "results": results}

@app.post("/api/curation/approve")
async def curation_approve(request: CurationActionRequest):
    """Approve an image for training dataset"""
    success = await dataset_quality_agent.approve_image(request.image_path)
    return {"success": success, "action": "approved", "path": request.image_path}

@app.post("/api/curation/reject")
async def curation_reject(request: CurationActionRequest):
    """Reject an image (archive or delete)"""
    success = await dataset_quality_agent.reject_image(request.image_path, delete=request.delete)
    return {"success": success, "action": "deleted" if request.delete else "archived", "path": request.image_path}

@app.post("/api/curation/reset-scores")
async def curation_reset_scores(persona: str = Query(default="starbright")):
    """Reset all scores to allow re-analysis with updated criteria"""
    result = dataset_quality_agent.reset_scores(persona)
    return result

@app.get("/api/curation/images")
async def curation_list_images(
    persona: str = Query(default="starbright"),
    filter_status: str = Query(default="all", description="Filter: all, pending, approved, rejected, review")
):
    """List all images with their curation status"""
    training_dir = Path("content/training") / persona.lower()
    images = []
    
    for f in sorted(training_dir.glob("*.png")) + sorted(training_dir.glob("*.jpg")):
        if f.name.startswith("ref_"):
            continue
        
        score_path = str(f).replace(".png", "_score.json").replace(".jpg", "_score.json")
        
        image_data = {
            "path": str(f),
            "filename": f.name,
            "url": f"/{f}",
            "status": "pending",
            "score": None,
            "recommendation": None,
            "face_match": None,
            "issues": []
        }
        
        if os.path.exists(score_path):
            try:
                with open(score_path, "r") as sf:
                    score_data = json.load(sf)
                    image_data.update({
                        "status": score_data.get("status", "pending"),
                        "score": score_data.get("score"),
                        "recommendation": score_data.get("recommendation"),
                        "face_match": score_data.get("face_match"),
                        "hair_match": score_data.get("hair_match"),
                        "body_match": score_data.get("body_match"),
                        "issues": score_data.get("issues", []),
                        "notes": score_data.get("notes", "")
                    })
            except:
                pass
        
        if filter_status == "all" or image_data["status"] == filter_status:
            images.append(image_data)
    
    return {"persona": persona, "images": images, "count": len(images)}


@app.get("/api/lora-review/images")
async def lora_review_list_images():
    """List images in the LoRA dataset review folder"""
    review_dir = Path("content/lora_dataset_review")
    if not review_dir.exists():
        return {"images": [], "count": 0}
    
    images = []
    for f in sorted(review_dir.glob("*.*")):
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            images.append({
                "filename": f.name,
                "path": str(f),
                "url": f"/api/lora-review/image/{f.name}",
                "size_kb": round(f.stat().st_size / 1024, 1)
            })
    
    return {"images": images, "count": len(images)}


@app.get("/api/lora-review/image/{filename}")
async def lora_review_serve_image(filename: str):
    """Serve a specific image from the review folder"""
    review_dir = Path("content/lora_dataset_review")
    file_path = review_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        file_path,
        headers={"Cache-Control": "no-cache"}
    )


@app.post("/api/lora-review/approve")
async def lora_review_approve(filenames: list[str] = None):
    """Move approved images to final training dataset"""
    review_dir = Path("content/lora_dataset_review")
    final_dir = Path("content/lora_final_training")
    final_dir.mkdir(parents=True, exist_ok=True)
    
    if filenames is None:
        # Approve all
        files = list(review_dir.glob("*.*"))
    else:
        files = [review_dir / f for f in filenames]
    
    approved = []
    for f in files:
        if f.exists() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            import shutil
            dest = final_dir / f.name
            shutil.copy2(f, dest)
            approved.append(f.name)
    
    return {"approved": len(approved), "files": approved, "destination": str(final_dir)}


@app.get("/api/calendar/generate/week")
async def calendar_generate_week(
    persona: str = Query(default="starbright_monroe", description="Persona name"),
    posts_per_day: int = Query(default=2, description="Posts per day (1-4)"),
    use_ai: bool = Query(default=True, description="Use AI optimization for captions")
):
    """Generate a week's content calendar with themed scheduling"""
    agent = get_calendar_agent(persona)
    calendar = await agent.generate_week_calendar(
        posts_per_day=min(posts_per_day, 4),
        use_ai_optimization=use_ai
    )
    return calendar


@app.get("/api/calendar/generate/month")
async def calendar_generate_month(
    persona: str = Query(default="starbright_monroe", description="Persona name"),
    year: int = Query(default=None, description="Year (default: current)"),
    month: int = Query(default=None, description="Month 1-12 (default: current)"),
    posts_per_day: int = Query(default=2, description="Posts per day (1-4)")
):
    """Generate a full month's content calendar"""
    from datetime import datetime
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    agent = get_calendar_agent(persona)
    calendar = await agent.generate_month_calendar(
        year=year,
        month=month,
        posts_per_day=min(posts_per_day, 4)
    )
    return calendar


@app.get("/api/calendar/list")
async def calendar_list(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """List all saved calendars"""
    agent = get_calendar_agent(persona)
    return {"calendars": agent.get_saved_calendars()}


@app.get("/api/calendar/load/{filename}")
async def calendar_load(
    filename: str,
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Load a specific calendar"""
    agent = get_calendar_agent(persona)
    calendar = agent.load_calendar(filename)
    if calendar:
        return calendar
    raise HTTPException(status_code=404, detail="Calendar not found")


@app.get("/api/calendar/today")
async def calendar_today(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Get today's scheduled posts"""
    agent = get_calendar_agent(persona)
    posts = agent.get_todays_posts()
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "day_name": datetime.now().strftime("%A"),
        "posts": posts
    }


@app.get("/api/calendar/themes")
async def calendar_themes(
    persona: str = Query(default="starbright_monroe", description="Persona name")
):
    """Get all theme configurations"""
    agent = get_calendar_agent(persona)
    return {"themes": agent.themes}


from app.agents.instagram_research_agent import instagram_research_agent

class ResearchRequest(BaseModel):
    username: str
    persona_name: str = "Starbright Monroe"
    persona_description: str = "pale ivory skin, slim athletic figure, dark brown hair, warm olive brown eyes"
    posts_limit: int = 30
    num_prompts: int = 15

@app.post("/api/research/analyze")
async def research_analyze_influencer(request: ResearchRequest):
    """
    Full research pipeline: scrape Instagram profile, analyze patterns, generate prompts.
    Requires APIFY_API_TOKEN secret.
    """
    result = await instagram_research_agent.full_research_pipeline(
        username=request.username,
        persona_name=request.persona_name,
        persona_description=request.persona_description,
        posts_limit=request.posts_limit,
        num_prompts=request.num_prompts
    )
    return result

@app.get("/api/research/scrape/{username}")
async def research_scrape_profile(
    username: str,
    posts_limit: int = Query(default=30, description="Number of posts to scrape")
):
    """Scrape Instagram profile and posts. Requires APIFY_API_TOKEN."""
    result = await instagram_research_agent.scrape_profile(username, posts_limit)
    return result

@app.post("/api/research/generate-prompts")
async def research_generate_prompts(
    username: str = Query(..., description="Instagram username to analyze"),
    persona_name: str = Query(default="Starbright Monroe"),
    persona_description: str = Query(default="pale ivory skin, slim athletic figure, dark brown hair, warm olive brown eyes"),
    num_prompts: int = Query(default=15)
):
    """Generate prompts from a previously scraped/analyzed profile."""
    scraped = await instagram_research_agent.scrape_profile(username)
    if not scraped.get("success"):
        return scraped
    
    analysis = await instagram_research_agent.analyze_content_patterns(scraped)
    if not analysis.get("success"):
        return analysis
    
    prompts = await instagram_research_agent.generate_prompts_from_analysis(
        analysis,
        persona_name=persona_name,
        persona_description=persona_description,
        num_prompts=num_prompts
    )
    return prompts

@app.get("/api/research/library")
async def research_get_library():
    """Get the full prompt library from all analyzed influencers."""
    return instagram_research_agent.load_prompt_library()

@app.get("/api/research/prompts")
async def research_get_prompts(
    category: str = Query(default=None, description="Filter by category (intimate, glamour, casual, fitness, portrait)")
):
    """Get prompts from library, optionally filtered by category."""
    prompts = instagram_research_agent.get_prompts_by_category(category)
    return {"prompts": prompts, "count": len(prompts)}

@app.get("/api/research/hooks")
async def research_get_hooks():
    """Get all caption hooks and engagement questions from library."""
    hooks = instagram_research_agent.get_engagement_hooks()
    return {"hooks": hooks, "count": len(hooks)}

@app.get("/api/research/status")
async def research_status():
    """Check Instagram Research Agent status and API availability."""
    import os
    return {
        "apify_configured": bool(os.getenv("APIFY_API_TOKEN")),
        "xai_configured": bool(os.getenv("XAI_API_KEY")),
        "cache_dir": str(instagram_research_agent.cache_dir),
        "prompt_library_exists": instagram_research_agent.prompt_library_path.exists(),
        "prompt_count": len(instagram_research_agent.get_prompts_by_category())
    }


class GenerateFromPromptRequest(BaseModel):
    prompt: str
    influencer_id: str = "starbright_monroe"
    caption_hook: Optional[str] = None
    provider: str = "fal"


BACKGROUND_MAPPING = {
    "beach": "content/backgrounds/beach_sunset.png",
    "pool": "content/backgrounds/infinity_pool_sunset.png",
    "gym": "content/backgrounds/gym_modern.png",
    "spa": "content/backgrounds/spa_wellness.png",
    "bathroom": "content/backgrounds/bathroom_luxury.png",
    "bedroom": "content/backgrounds/apartment_bedroom_day.png",
    "night": "content/backgrounds/apartment_night.png",
    "apartment": "content/backgrounds/apartment_day.png",
    "living": "content/backgrounds/apartment_day.png",
    "cafe": "content/backgrounds/apartment_day.png",
    "coffee": "content/backgrounds/apartment_day.png",
    "morning": "content/backgrounds/apartment_bedroom_day.png",
    "sunset": "content/backgrounds/beach_sunset.png",
    "luxury": "content/backgrounds/apartment_day.png",
}

def select_background_from_prompt(prompt: str) -> str:
    """Select an appropriate background based on prompt keywords."""
    import random
    prompt_lower = prompt.lower()
    
    for keyword, bg_path in BACKGROUND_MAPPING.items():
        if keyword in prompt_lower:
            return bg_path
    
    all_backgrounds = list(set(BACKGROUND_MAPPING.values()))
    return random.choice(all_backgrounds)


def select_aspect_ratio_from_prompt(prompt: str) -> str:
    """
    Dynamically select the best aspect ratio based on pose keywords.
    
    Returns:
        Aspect ratio string: "9:16", "16:9", "3:4", "4:3", or "1:1"
    """
    prompt_lower = prompt.lower()
    
    horizontal_keywords = [
        "lying down", "lying on", "on her stomach", "on her back", "on her side",
        "sprawled", "stretched out", "reclined", "reclining", "lounging horizontally",
        "on the bed", "in bed", "crawling"
    ]
    for keyword in horizontal_keywords:
        if keyword in prompt_lower:
            return "16:9"
    
    square_keywords = [
        "close-up", "closeup", "headshot", "face shot", "portrait shot",
        "upper body", "bust shot", "shoulders up"
    ]
    for keyword in square_keywords:
        if keyword in prompt_lower:
            return "1:1"
    
    medium_vertical_keywords = [
        "sitting", "seated", "kneeling", "bent over", "leaning forward",
        "crouching", "squatting", "on all fours", "crossed legs"
    ]
    for keyword in medium_vertical_keywords:
        if keyword in prompt_lower:
            return "3:4"
    
    return "9:16"


def restructure_research_prompt(narrative_prompt: str) -> tuple:
    """
    Convert a narrative research prompt into Seedream4's optimal format:
    [Context] → [Subject] → [Style intent] → [Constraints]
    
    Adds realism enforcers and pose/accessory variation.
    Note: Seedream4 doesn't support negative_prompt, so we use positive phrasing.
    """
    from app.services.prompt_variation_service import prompt_variation_service, enhance_outfit_prompt
    import re
    
    specific_pose_patterns = [
        (r"lying on (?:her |his )?(?:stomach|back|side)", "full body shot from head to feet, lying on her stomach, legs extended behind"),
        (r"sitting on (?:the |a |her )?(?:bed|couch|sofa|chair|floor)", "full body sitting pose showing entire figure"),
        (r"kneeling", "full body kneeling pose"),
        (r"crawling", "full body crawling pose showing entire figure"),
        (r"bent over", "full body bent over pose"),
        (r"on all fours", "full body on all fours pose showing entire figure"),
    ]
    
    narrative_pose = None
    prompt_lower = narrative_prompt.lower()
    for pattern, full_pose in specific_pose_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            narrative_pose = full_pose
            break
    
    variation = prompt_variation_service.get_next_variation(narrative_prompt)
    
    identity = "fashion model with very pale porcelain ivory white skin, extremely thin slender petite body, very narrow tiny waist, slim narrow hips, long thin slender legs, delicate small frame, size 0 figure, long flowing dark brown hair, warm olive brown eyes"
    
    body_reinforcement = "ultra-slim waiflike physique, visible collarbones, slender arms, fair complexion"
    
    if narrative_pose:
        pose_expression = narrative_pose
        if variation["expression"]:
            pose_expression = f"{narrative_pose}, {variation['expression']}"
        logger.info(f"Using narrative pose: {narrative_pose}")
    else:
        pose_expression = variation["pose"]
        if variation["expression"]:
            pose_expression = f"{variation['pose']}, {variation['expression']}"
    
    earring_positive = variation["earring_positive"]
    earring_negative = variation["earring_negative"]
    
    hyperreal_camera = "shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field"
    hyperreal_skin = "natural skin texture with visible pores, fine skin detail, slight natural skin imperfections, photorealistic skin tones, real human photography"
    hyperreal_quality = "8K ultra detailed, cinematic color grading, editorial portrait, natural ambient lighting, soft bokeh background"
    hyperreal_anti = "no plastic skin, no airbrushed, no over-smoothed, no beauty filter, no CGI, no 3D render, clean uncluttered background, natural environment"
    
    prompt_lower = narrative_prompt.lower()
    
    import re
    
    pose_gaze_conflicts = [
        "gazing at the water's reflection",
        "gazing at", "looking at", "staring at", "watching",
        "looking down", "looking up", "looking away",
        "hand on her waist", "hand on waist", "hands on hips",
        "standing with one hand on her waist",
        "standing with", "posing with", "leaning against",
        "one hand on her waist", "one hand on", "both hands on",
        "the water's reflection", "water's reflection",
        "reflection", "gazing into", "eyes on",
        "by a poolside", "by the pool", "in the pool", "poolside at",
        "in the water", "standing in water", "posing by a pool"
    ]
    cleaned_prompt = narrative_prompt
    for conflict in sorted(pose_gaze_conflicts, key=len, reverse=True):
        pattern = re.compile(re.escape(conflict), re.IGNORECASE)
        cleaned_prompt = pattern.sub("", cleaned_prompt)
    
    cleaned_prompt = re.sub(r'\s+', ' ', cleaned_prompt).strip()
    cleaned_prompt = re.sub(r',\s*,', ',', cleaned_prompt)
    cleaned_prompt = re.sub(r'\.\s*\.', '.', cleaned_prompt)
    cleaned_prompt = re.sub(r"'\s*$", "", cleaned_prompt)
    cleaned_prompt = re.sub(r",\s*$", "", cleaned_prompt)
    
    prompt_lower = cleaned_prompt.lower()
    
    outfit = ""
    scene = ""
    lighting = ""
    
    outfit_keywords = ["wears a", "wearing a", "dressed in a", "dressed in", "wearing"]
    for kw in outfit_keywords:
        if kw in prompt_lower:
            start = prompt_lower.find(kw) + len(kw)
            end = min(start + 100, len(cleaned_prompt))
            segment = cleaned_prompt[start:end].strip()
            if ". " in segment:
                segment = segment[:segment.find(". ")]
            outfit = segment.strip()
            break
    
    if not outfit:
        garment_keywords = ["dress", "gown", "bikini", "swimwear", "outfit", "suit"]
        for gk in garment_keywords:
            if gk in prompt_lower:
                idx = prompt_lower.find(gk)
                start = max(0, idx - 30)
                end = min(idx + len(gk) + 20, len(cleaned_prompt))
                segment = cleaned_prompt[start:end].strip()
                if "." in segment:
                    segment = segment[:segment.find(".")]
                outfit = segment.strip()
                break
    
    outfit = enhance_outfit_prompt(outfit)
    
    scene_keywords = ["setting is", "background", "in the", "at the", "on a", "rooftop", "lounge", "beach", "gym", "apartment"]
    for kw in scene_keywords:
        if kw in prompt_lower:
            start = prompt_lower.find(kw)
            end = min(start + 100, len(cleaned_prompt))
            segment = cleaned_prompt[start:end]
            if "." in segment:
                segment = segment[:segment.find(".")]
            scene = segment.strip()
            break
    
    if scene:
        scene = re.sub(r'\bpool\b', 'outdoor terrace', scene, flags=re.IGNORECASE)
        scene = re.sub(r'\bpoolside\b', 'outdoor terrace', scene, flags=re.IGNORECASE)
    
    if "neon" in prompt_lower:
        lighting = "neon lighting with blue and pink glow, high contrast"
    elif "golden hour" in prompt_lower or "sunset" in prompt_lower:
        lighting = "golden hour warm lighting"
    elif "natural" in prompt_lower:
        lighting = "natural daylight"
    else:
        lighting = "cinematic studio lighting"
    
    structured_parts = [
        hyperreal_camera,
        identity,
        body_reinforcement,
        pose_expression,
        earring_positive,
        outfit if outfit else "elegant outfit",
        scene if scene else "luxurious interior setting",
        lighting,
        hyperreal_skin,
        hyperreal_quality,
        hyperreal_anti
    ]
    
    logger.info(f"Variation applied: pose='{variation['pose']}', earring='{earring_positive}', outfit='{outfit}'")
    
    aspect_ratio = select_aspect_ratio_from_prompt(narrative_prompt)
    logger.info(f"Dynamic aspect ratio selected: {aspect_ratio}")
    
    final_prompt = ", ".join([p for p in structured_parts if p])
    return final_prompt, aspect_ratio


@app.post("/api/research/generate-from-prompt")
async def research_generate_from_prompt(request: GenerateFromPromptRequest):
    """
    Generate an image from a research prompt.
    Supports two providers:
    - fal: Uses fal.ai Seedream 4.5 edit endpoint with reference conditioning (default)
    - replicate: Uses Replicate Seedream 4.5 (legacy)
    """
    try:
        logger.info(f"=== GENERATE FROM PROMPT RECEIVED ===")
        logger.info(f"Provider: {request.provider}, Prompt length: {len(request.prompt)}, Influencer: {request.influencer_id}")
        
        original_prompt = request.prompt
        
        if request.provider == "fal":
            from app.services.fal_seedream_service import FalSeedreamService
            
            logger.info("Using fal.ai Seedream 4.5 with reference conditioning...")
            fal_service = FalSeedreamService()
            
            aspect_ratio = select_aspect_ratio_from_prompt(original_prompt)
            fal_aspect = {
                "9:16": "portrait_4_3",
                "16:9": "landscape_16_9",
                "3:4": "portrait_4_3",
                "4:3": "landscape_4_3",
                "1:1": "square"
            }.get(aspect_ratio, "portrait_4_3")
            
            logger.info(f"Aspect ratio: {aspect_ratio} -> {fal_aspect}")
            
            result = await fal_service.generate_from_research_prompt(
                narrative_prompt=original_prompt,
                influencer_id=request.influencer_id,
                aspect_ratio=fal_aspect
            )
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "image_path": result.get("image_path"),
                    "prompt_used": original_prompt,
                    "caption_hook": request.caption_hook,
                    "original_prompt": original_prompt,
                    "provider": "fal.ai"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Generation failed"),
                    "provider": "fal.ai"
                }
        
        else:
            from app.agents.unified_content_agent import PromptSafetyFilter
            from app.services.seedream4_service import Seedream4Service
            
            logger.info("Using Replicate Seedream 4.5 (legacy)...")
            
            restructured_prompt, aspect_ratio = restructure_research_prompt(original_prompt)
            safe_prompt, substitutions = PromptSafetyFilter.sanitize_prompt(restructured_prompt)
            
            if substitutions:
                logger.info(f"Prompt sanitized with {len(substitutions)} substitutions")
            
            is_valid, validation_error = PromptSafetyFilter.validate_prompt(safe_prompt)
            if not is_valid:
                return {"success": False, "error": f"Prompt validation failed: {validation_error}"}
            
            seedream = Seedream4Service()
            result = await seedream.generate(
                prompt=safe_prompt,
                aspect_ratio=aspect_ratio,
                filename_prefix="research",
                size="4K"
            )
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "image_path": result.get("image_path"),
                    "prompt_used": safe_prompt,
                    "caption_hook": request.caption_hook,
                    "original_prompt": original_prompt,
                    "provider": "replicate"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Generation failed"),
                    "provider": "replicate"
                }
                
    except Exception as e:
        logger.error(f"=== GENERATION ERROR: {str(e)} ===")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


class BatchGenerateRequest(BaseModel):
    prompts: list[str]
    influencer_id: str = "starbright_monroe"
    provider: str = "fal"
    consistency_mode: bool = False
    background: str = "luxury_apartment"
    lighting: str = "soft studio lighting from above"


@app.post("/api/research/generate-batch")
async def research_generate_batch(request: BatchGenerateRequest):
    """
    Generate multiple images sequentially from a list of prompts.
    Supports fal.ai (default) and replicate providers.
    
    When consistency_mode=True, overrides background/lighting for all images.
    Available backgrounds: luxury_apartment, studio_white, studio_dark, bedroom
    """
    results = []
    total = len(request.prompts)
    
    mode_label = "CONSISTENCY MODE" if request.consistency_mode else "CREATIVE MODE"
    logger.info(f"=== BATCH GENERATION STARTED: {total} prompts, {mode_label}, provider: {request.provider} ===")
    if request.consistency_mode:
        logger.info(f"Background: {request.background}, Lighting: {request.lighting}")
    
    if request.provider == "fal":
        from app.services.fal_seedream_service import FalSeedreamService
        fal_service = FalSeedreamService(request.influencer_id)
        
        for idx, prompt in enumerate(request.prompts, 1):
            logger.info(f"Batch [{idx}/{total}]: Generating with fal.ai ({mode_label})...")
            
            try:
                if request.consistency_mode:
                    result = await fal_service.generate_consistency_from_prompt(
                        narrative_prompt=prompt,
                        background=request.background,
                        lighting=request.lighting,
                        aspect_ratio="portrait_4_3"
                    )
                else:
                    aspect_ratio = select_aspect_ratio_from_prompt(prompt)
                    fal_aspect = {
                        "9:16": "portrait_4_3", "16:9": "landscape_16_9",
                        "3:4": "portrait_4_3", "4:3": "landscape_4_3", "1:1": "square"
                    }.get(aspect_ratio, "portrait_4_3")
                    
                    result = await fal_service.generate_from_research_prompt(
                        narrative_prompt=prompt,
                        influencer_id=request.influencer_id,
                        aspect_ratio=fal_aspect
                    )
                
                if result.get("status") == "success":
                    logger.info(f"Batch [{idx}/{total}]: Success - {result.get('image_path')}")
                    results.append({
                        "index": idx, "success": True,
                        "image_path": result.get("image_path"),
                        "original_prompt": prompt, "provider": "fal.ai",
                        "consistency_mode": request.consistency_mode
                    })
                else:
                    results.append({
                        "index": idx, "success": False,
                        "error": result.get("error", "Generation failed"),
                        "original_prompt": prompt
                    })
            except Exception as e:
                results.append({"index": idx, "success": False, "error": str(e), "original_prompt": prompt})
    else:
        from app.agents.unified_content_agent import PromptSafetyFilter
        from app.services.seedream4_service import Seedream4Service
        
        for idx, prompt in enumerate(request.prompts, 1):
            logger.info(f"Batch [{idx}/{total}]: Generating with Replicate...")
            try:
                restructured_prompt, aspect_ratio = restructure_research_prompt(prompt)
                safe_prompt, _ = PromptSafetyFilter.sanitize_prompt(restructured_prompt)
                
                is_valid, validation_error = PromptSafetyFilter.validate_prompt(safe_prompt)
                if not is_valid:
                    results.append({"index": idx, "success": False, "error": f"Validation failed: {validation_error}", "original_prompt": prompt})
                    continue
                
                seedream = Seedream4Service()
                result = await seedream.generate(prompt=safe_prompt, aspect_ratio=aspect_ratio, filename_prefix="research", size="4K")
                
                if result.get("status") == "success":
                    results.append({"index": idx, "success": True, "image_path": result.get("image_path"), "original_prompt": prompt, "provider": "replicate"})
                else:
                    results.append({"index": idx, "success": False, "error": result.get("error", "Generation failed"), "original_prompt": prompt})
            except Exception as e:
                results.append({"index": idx, "success": False, "error": str(e), "original_prompt": prompt})
    
    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"=== BATCH COMPLETE: {successful}/{total} successful ===")
    
    return {"total": total, "successful": successful, "failed": total - successful, "results": results}


class ConsistencyBatchRequest(BaseModel):
    poses: list[str]
    outfits: list[str]
    background: str = "luxury_apartment"
    lighting: str = "soft natural daylight"
    influencer_id: str = "starbright_monroe"


@app.post("/api/research/generate-consistency-batch")
async def research_generate_consistency_batch(request: ConsistencyBatchRequest):
    """
    Generate images in consistency mode with locked background and no accessories.
    
    Combines each pose with each outfit for a cartesian product of images.
    All images use the same background and have earrings/jewelry suppressed.
    
    Available backgrounds: luxury_apartment, studio_white, studio_dark, bedroom
    """
    from app.services.fal_seedream_service import FalSeedreamService
    
    fal_service = FalSeedreamService(request.influencer_id)
    results = []
    
    combinations = [(pose, outfit) for pose in request.poses for outfit in request.outfits]
    total = len(combinations)
    
    logger.info(f"=== CONSISTENCY BATCH: {total} images ({len(request.poses)} poses x {len(request.outfits)} outfits) ===")
    logger.info(f"Background: {request.background}, Lighting: {request.lighting}")
    
    for idx, (pose, outfit) in enumerate(combinations, 1):
        logger.info(f"Consistency [{idx}/{total}]: pose='{pose[:50]}...', outfit='{outfit[:30]}...'")
        
        try:
            result = await fal_service.generate_consistency_mode(
                pose=pose,
                outfit=outfit,
                background=request.background,
                lighting=request.lighting,
                aspect_ratio="portrait_4_3"
            )
            
            if result.get("status") == "success":
                logger.info(f"Consistency [{idx}/{total}]: Success - {result.get('image_path')}")
                results.append({
                    "index": idx,
                    "success": True,
                    "image_path": result.get("image_path"),
                    "pose": pose,
                    "outfit": outfit,
                    "background": request.background
                })
            else:
                results.append({
                    "index": idx,
                    "success": False,
                    "error": result.get("error", "Generation failed"),
                    "pose": pose,
                    "outfit": outfit
                })
        except Exception as e:
            logger.error(f"Consistency [{idx}/{total}]: Error - {str(e)}")
            results.append({
                "index": idx,
                "success": False,
                "error": str(e),
                "pose": pose,
                "outfit": outfit
            })
    
    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"=== CONSISTENCY BATCH COMPLETE: {successful}/{total} successful ===")
    
    return {
        "total": total,
        "successful": successful,
        "failed": total - successful,
        "background": request.background,
        "results": results
    }


# ============================================================
# LORA GENERATION API
# ============================================================

class LoraUploadResponse(BaseModel):
    status: str
    lora_url: Optional[str] = None
    file_name: Optional[str] = None
    error: Optional[str] = None

class LoraGenerateRequest(BaseModel):
    prompt: str
    lora_url: Optional[str] = None
    lora_scale: float = 1.0
    image_size: str = "portrait_4_3"
    num_inference_steps: int = 28
    guidance_scale: float = 3.5
    num_images: int = 1

class SdxlLoraGenerateRequest(BaseModel):
    prompt: str
    lora_url: Optional[str] = None
    lora_scale: float = 1.0
    negative_prompt: str = "blurry, low quality, distorted, deformed"
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    num_images: int = 1
    width: int = 768
    height: int = 1024

class IdentityTransferRequest(BaseModel):
    source_image_url: str
    face_reference_url: Optional[str] = None
    prompt: str = "professional photography, natural lighting, 8K quality"
    negative_prompt: str = "nsfw, lowres, bad anatomy, bad hands, blurry, deformed"
    ip_adapter_scale: float = 0.8
    identity_controlnet_conditioning_scale: float = 0.8
    num_inference_steps: int = 8

class BatchIdentityTransferRequest(BaseModel):
    source_image_urls: list[str]
    face_reference_url: Optional[str] = None
    prompt: str = "professional photography, natural lighting"

@app.post("/api/lora/upload")
async def upload_lora(file: UploadFile = File(...)):
    """Upload a safetensor LoRA file to Fal.ai storage"""
    from app.services.fal_lora_service import FalLoraService
    
    if not file.filename.endswith(".safetensors"):
        raise HTTPException(status_code=400, detail="Only .safetensors files are supported")
    
    temp_path = Path(f"content/temp_{file.filename}")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        content = await file.read()
        temp_path.write_bytes(content)
        
        service = FalLoraService()
        result = await service.upload_lora(str(temp_path))
        
        temp_path.unlink(missing_ok=True)
        
        if result.get("status") == "success":
            return LoraUploadResponse(
                status="success",
                lora_url=result.get("lora_url"),
                file_name=result.get("file_name")
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lora/generate")
async def generate_with_lora(request: LoraGenerateRequest):
    """Generate images using a custom LoRA with Fal.ai Flux-LoRA"""
    from app.services.fal_lora_service import FalLoraService
    
    if not request.lora_url:
        raise HTTPException(status_code=400, detail="lora_url is required. Upload a LoRA first using /api/lora/upload")
    
    service = FalLoraService()
    result = await service.generate_with_lora(
        prompt=request.prompt,
        lora_url=request.lora_url,
        lora_scale=request.lora_scale,
        image_size=request.image_size,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
        num_images=request.num_images
    )
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "images": result.get("images", []),
            "seed": result.get("seed"),
            "lora_scale": result.get("lora_scale")
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

@app.post("/api/lora/generate-sdxl")
async def generate_with_sdxl_lora(request: SdxlLoraGenerateRequest):
    """Generate images using a custom LoRA with Fal.ai SDXL LoRA (better for SDXL-trained LoRAs)"""
    from app.services.fal_lora_service import FalLoraService
    
    if not request.lora_url:
        raise HTTPException(status_code=400, detail="lora_url is required. Upload a LoRA first using /api/lora/upload")
    
    service = FalLoraService()
    result = await service.generate_with_sdxl_lora(
        prompt=request.prompt,
        lora_url=request.lora_url,
        lora_scale=request.lora_scale,
        negative_prompt=request.negative_prompt,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
        num_images=request.num_images,
        image_size={"width": request.width, "height": request.height}
    )
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "images": result.get("images", []),
            "seed": result.get("seed"),
            "model": "sdxl-lora",
            "lora_scale": result.get("lora_scale")
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

@app.get("/api/lora/status")
async def lora_status():
    """Check LoRA service status and available LoRA files"""
    lora_dir = Path("attached_assets")
    lora_files = list(lora_dir.glob("*.safetensors")) if lora_dir.exists() else []
    
    return {
        "status": "ready",
        "fal_key_configured": bool(os.getenv("FAL_KEY")),
        "available_lora_files": [f.name for f in lora_files],
        "endpoint_upload": "/api/lora/upload",
        "endpoint_generate": "/api/lora/generate"
    }

@app.post("/api/identity/transfer")
async def identity_transfer(request: IdentityTransferRequest):
    """Transfer Starbright's identity onto a source image using InstantID"""
    from app.services.fal_instantid_service import FalInstantIDService
    
    service = FalInstantIDService()
    result = await service.transfer_identity(
        source_image_url=request.source_image_url,
        face_reference_url=request.face_reference_url,
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        ip_adapter_scale=request.ip_adapter_scale,
        identity_controlnet_conditioning_scale=request.identity_controlnet_conditioning_scale,
        num_inference_steps=request.num_inference_steps
    )
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "image": result.get("image"),
            "seed": result.get("seed"),
            "model": "instantid-lcm"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Identity transfer failed"))

@app.post("/api/identity/batch-transfer")
async def batch_identity_transfer(request: BatchIdentityTransferRequest):
    """Batch transfer Starbright's identity onto multiple source images"""
    from app.services.fal_instantid_service import FalInstantIDService
    
    service = FalInstantIDService()
    result = await service.batch_transfer(
        source_images=request.source_image_urls,
        face_reference_url=request.face_reference_url,
        prompt=request.prompt
    )
    
    return result

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

@app.post("/api/identity/upload-and-transfer")
async def upload_and_identity_transfer(
    file: UploadFile = File(...),
    prompt: str = "professional photography, natural lighting"
):
    """Upload a local image and transfer Starbright's identity onto it"""
    from app.services.fal_instantid_service import FalInstantIDService
    import uuid
    
    ext = Path(file.filename or '').suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    
    safe_filename = f"{uuid.uuid4()}{ext}"
    temp_path = Path(f"/tmp/{safe_filename}")
    try:
        content = await file.read()
        temp_path.write_bytes(content)
        
        service = FalInstantIDService()
        result = await service.upload_and_transfer(
            source_image_path=str(temp_path),
            prompt=prompt
        )
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "image": result.get("image"),
                "seed": result.get("seed")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Transfer failed"))
    finally:
        temp_path.unlink(missing_ok=True)

@app.get("/api/identity/status")
async def identity_transfer_status():
    """Check identity transfer service status"""
    starbright_ref = Path("content/references/starbright_monroe/body_reference_canonical.png")
    return {
        "status": "ready",
        "fal_key_configured": bool(os.getenv("FAL_KEY")),
        "starbright_reference_available": starbright_ref.exists(),
        "output_dir": "content/generated/identity_transfer",
        "endpoints": {
            "transfer": "/api/identity/transfer",
            "batch": "/api/identity/batch-transfer",
            "upload": "/api/identity/upload-and-transfer",
            "pipeline": "/api/identity/pipeline"
        }
    }


@app.post("/api/identity/pipeline")
async def identity_pipeline(
    username: str = Form(...),
    max_images: int = Form(5),
    prompt: str = Form("professional photography, natural lighting, 8K quality"),
    ip_adapter_scale: float = Form(0.6),
    controlnet_conditioning_scale: float = Form(0.8),
    identity_controlnet_conditioning_scale: float = Form(0.8),
    num_inference_steps: int = Form(12)
):
    """
    Full pipeline: Scrape influencer images → Transfer Starbright's identity
    
    1. Scrapes Instagram profile using Apify
    2. Downloads top images
    3. Transfers Starbright's identity onto each image
    
    Parameters:
    - ip_adapter_scale: Face identity strength (0.0-1.0, lower = more source preservation)
    - controlnet_conditioning_scale: Pose/outfit preservation (0.0-1.0, higher = more source)
    - identity_controlnet_conditioning_scale: Facial landmark control
    - num_inference_steps: Quality (8-20, higher = better)
    """
    from app.agents.instagram_research_agent import InstagramResearchAgent
    from app.services.fal_instantid_service import FalInstantIDService
    
    research_agent = InstagramResearchAgent()
    identity_service = FalInstantIDService()
    
    # Step 1: Scrape profile
    logger.info(f"Pipeline: Scraping @{username}...")
    scraped_data = await research_agent.scrape_profile(username, posts_limit=max_images * 2)
    
    if not scraped_data.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to scrape profile: {scraped_data.get('error')}"
        )
    
    # Step 2: Download images
    logger.info(f"Pipeline: Downloading images from @{username}...")
    image_paths = await research_agent.download_post_images(scraped_data, max_images=max_images)
    
    if not image_paths:
        raise HTTPException(
            status_code=400,
            detail="No images found to process"
        )
    
    # Step 3: Transfer identity to each image
    logger.info(f"Pipeline: Transferring identity to {len(image_paths)} images...")
    results = {
        "status": "success",
        "username": username,
        "processed": 0,
        "failed": 0,
        "images": [],
        "errors": []
    }
    
    for i, source_path in enumerate(image_paths):
        logger.info(f"Processing image {i+1}/{len(image_paths)}: {source_path}")
        
        result = await identity_service.upload_and_transfer(
            source_image_path=source_path,
            prompt=prompt,
            filename_prefix=f"{username}_{i+1:03d}",
            ip_adapter_scale=ip_adapter_scale,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            identity_controlnet_conditioning_scale=identity_controlnet_conditioning_scale,
            num_inference_steps=num_inference_steps
        )
        
        if result.get("status") == "success":
            results["processed"] += 1
            results["images"].append({
                "source": source_path,
                "output": result.get("image"),
                "seed": result.get("seed")
            })
        else:
            results["failed"] += 1
            results["errors"].append({
                "source": source_path,
                "error": result.get("error")
            })
    
    if results["failed"] > 0 and results["processed"] == 0:
        results["status"] = "error"
    elif results["failed"] > 0:
        results["status"] = "partial"
    
    return results


@app.post("/api/identity/pipeline-urls")
async def identity_pipeline_urls(
    image_urls: list[str] = Body(...),
    prompt: str = Body("professional photography, natural lighting, 8K quality")
):
    """
    Transfer Starbright's identity to provided image URLs.
    
    Use this when you already have image URLs (e.g., from manual research).
    """
    from app.services.fal_instantid_service import FalInstantIDService
    
    if not image_urls:
        raise HTTPException(status_code=400, detail="No image URLs provided")
    
    identity_service = FalInstantIDService()
    
    result = await identity_service.batch_transfer(
        source_images=image_urls,
        prompt=prompt
    )
    
    return result


# =============================================================================
# POSE TRANSFER ENDPOINTS (Leffa Pose Transfer)
# =============================================================================

class PoseTransferRequest(BaseModel):
    pose_image_url: str
    person_image_url: Optional[str] = None
    num_inference_steps: int = 50
    guidance_scale: float = 2.5
    seed: Optional[int] = None

class BatchPoseTransferRequest(BaseModel):
    pose_image_urls: list[str]
    person_image_url: Optional[str] = None
    num_inference_steps: int = 50
    guidance_scale: float = 2.5


@app.post("/api/pose/transfer")
async def pose_transfer(request: PoseTransferRequest):
    """
    Transfer pose from source image to Starbright's identity using Leffa Pose Transfer.
    
    Parameters:
    - pose_image_url: Image with the desired pose
    - person_image_url: Starbright reference (auto-detected if not provided)
    - num_inference_steps: More steps = higher quality (default: 50)
    - guidance_scale: CFG scale (default: 2.5)
    """
    from app.services.fal_pose_transfer_service import fal_pose_transfer_service
    
    result = await fal_pose_transfer_service.transfer_pose(
        pose_image_url=request.pose_image_url,
        person_image_url=request.person_image_url,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
        seed=request.seed
    )
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "image": result.get("image"),
            "seed": result.get("seed"),
            "model": "leffa-pose-transfer"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Pose transfer failed"))


@app.post("/api/pose/batch-transfer")
async def batch_pose_transfer(request: BatchPoseTransferRequest):
    """Batch transfer poses to Starbright's identity"""
    from app.services.fal_pose_transfer_service import fal_pose_transfer_service
    
    result = await fal_pose_transfer_service.batch_transfer(
        pose_images=request.pose_image_urls,
        person_image_url=request.person_image_url,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale
    )
    
    return result


@app.post("/api/pose/upload-and-transfer")
async def upload_and_pose_transfer(
    file: UploadFile = File(...),
    num_inference_steps: int = Form(50),
    guidance_scale: float = Form(2.5)
):
    """Upload a local pose image and transfer it to Starbright's identity"""
    from app.services.fal_pose_transfer_service import fal_pose_transfer_service
    import uuid
    
    ext = Path(file.filename or '').suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    
    safe_filename = f"{uuid.uuid4()}{ext}"
    temp_path = Path(f"/tmp/{safe_filename}")
    try:
        content = await file.read()
        temp_path.write_bytes(content)
        
        result = await fal_pose_transfer_service.upload_and_transfer(
            pose_image_path=str(temp_path),
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        )
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "image": result.get("image"),
                "seed": result.get("seed")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Transfer failed"))
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/api/pose/status")
async def pose_transfer_status():
    """Check pose transfer service status"""
    starbright_ref = Path("content/references/starbright_monroe/body_reference_canonical.png")
    alt_ref = Path("content/references/starbright_monroe/canonical_face/face_01.png")
    
    return {
        "status": "ready",
        "fal_key_configured": bool(os.getenv("FAL_KEY")),
        "starbright_reference_available": starbright_ref.exists() or alt_ref.exists(),
        "output_dir": "content/generated/pose_transfer",
        "method": "Leffa Pose Transfer (fal-ai/leffa/pose-transfer)",
        "endpoints": {
            "transfer": "/api/pose/transfer",
            "batch": "/api/pose/batch-transfer",
            "upload": "/api/pose/upload-and-transfer",
            "test": "/api/pose/test-ia-love2"
        },
        "parameters": {
            "num_inference_steps": "10-100 (higher = better quality, slower)",
            "guidance_scale": "1.0-5.0 (how closely to follow guidance)"
        }
    }


@app.post("/api/pose/test-ia-love2")
async def test_pose_transfer_ia_love2(
    image_index: int = Query(1, ge=1, le=3, description="Image to test (1, 2, or 3)"),
    num_inference_steps: int = Query(50, ge=10, le=100),
    guidance_scale: float = Query(2.5, ge=1.0, le=5.0)
):
    """
    Quick test endpoint using ia_love2 research images.
    
    Available images:
    - 1: Selfie maid outfit
    - 2: Bunny costume sitting  
    - 3: Car interior laughing
    """
    from app.services.fal_pose_transfer_service import fal_pose_transfer_service
    
    image_paths = {
        1: "content/research_images/ia_love2/post_1.jpg",
        2: "content/research_images/ia_love2/post_2.jpg",
        3: "content/research_images/ia_love2/post_3.jpg"
    }
    
    image_path = image_paths.get(image_index)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Test image {image_index} not found")
    
    result = await fal_pose_transfer_service.upload_and_transfer(
        pose_image_path=image_path,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale
    )
    
    return result


from app.services.prompt_intelligence_service import prompt_intelligence_service

@app.get("/api/prompt-intelligence")
async def get_prompt_intelligence_status():
    """Get Prompt Intelligence Service status"""
    return {
        "service": "PromptIntelligenceService",
        "status": "active",
        "models": {
            "cogvlm": "cjwbw/cogvlm (Replicate)",
            "clip_interrogator": "pharmapsychotic/clip-interrogator (Replicate)",
            "grok_vision": "grok-2-vision (XAI)"
        },
        "endpoints": {
            "analyze_cogvlm": "/api/prompt-intelligence/analyze/cogvlm",
            "analyze_clip": "/api/prompt-intelligence/analyze/clip",
            "analyze_grok": "/api/prompt-intelligence/analyze/grok",
            "full_analysis": "/api/prompt-intelligence/analyze/full",
            "generate_prompt": "/api/prompt-intelligence/generate-prompt",
            "test": "/api/prompt-intelligence/test-ia-love2"
        }
    }


@app.post("/api/prompt-intelligence/analyze/cogvlm")
async def analyze_with_cogvlm(
    image_path: str,
    prompt: str = "Describe this image in comprehensive detail. Include: the person's pose, body position, facial expression, outfit/clothing with colors and materials, hairstyle, makeup, setting/background, lighting conditions, camera angle, and overall mood/aesthetic."
):
    """Analyze image with CogVLM for detailed scene description"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.analyze_with_cogvlm(image_path, prompt)


@app.post("/api/prompt-intelligence/analyze/clip")
async def analyze_with_clip(
    image_path: str,
    mode: str = "best"
):
    """Analyze image with CLIP Interrogator for aesthetic/style tags"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.analyze_with_clip_interrogator(image_path, mode)


@app.post("/api/prompt-intelligence/analyze/grok")
async def analyze_with_grok(
    image_path: str,
    focus: str = "influencer_content"
):
    """Analyze image with Grok Vision for high-level understanding"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.analyze_with_grok_vision(image_path, focus)


@app.post("/api/prompt-intelligence/analyze/full")
async def full_image_analysis(
    image_path: str,
    include_clip: bool = True,
    include_grok: bool = True
):
    """Run comprehensive analysis using all available models"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.full_analysis(image_path, include_clip, include_grok)


@app.post("/api/prompt-intelligence/generate-prompt")
async def generate_seedream_prompt(
    image_path: str,
    persona: str = "starbright_monroe"
):
    """Generate optimized Seedream 4.5 prompt from competitor image"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.generate_seedream_prompt(image_path, persona)


@app.post("/api/prompt-intelligence/generate-prompt-fast")
async def generate_seedream_prompt_fast(
    image_path: str,
    persona: str = "starbright_monroe"
):
    """Generate detailed Seedream 4.5 prompt using Grok Vision only (fast, no Replicate cold-start)"""
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    return await prompt_intelligence_service.generate_seedream_prompt_fast(image_path, persona)


@app.post("/api/prompt-intelligence/test-ia-love2")
async def test_prompt_intelligence_ia_love2(
    image_index: int = 1,
    model: str = "cogvlm"
):
    """Test prompt intelligence with ia_love2 research images"""
    image_paths = {
        1: "content/research_images/ia_love2/post_1.jpg",
        2: "content/research_images/ia_love2/post_2.jpg",
        3: "content/research_images/ia_love2/post_3.jpg"
    }
    
    image_path = image_paths.get(image_index)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Test image {image_index} not found")
    
    if model == "cogvlm":
        return await prompt_intelligence_service.analyze_with_cogvlm(image_path)
    elif model == "clip":
        return await prompt_intelligence_service.analyze_with_clip_interrogator(image_path)
    elif model == "grok":
        return await prompt_intelligence_service.analyze_with_grok_vision(image_path)
    elif model == "full":
        return await prompt_intelligence_service.full_analysis(image_path)
    elif model == "prompt":
        return await prompt_intelligence_service.generate_seedream_prompt(image_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}. Use: cogvlm, clip, grok, full, or prompt")


@app.post("/api/prompt-intelligence/generate-from-competitor")
async def generate_from_competitor_image(
    competitor_image: str,
    persona: str = "starbright_monroe",
    aspect_ratio: str = "portrait_4_3"
):
    """
    End-to-end workflow: Analyze competitor image → Generate prompt → Create new image
    
    This integrates PromptIntelligenceService with FalSeedreamService for
    one-step competitor-inspired image generation.
    
    Accepts both local file paths and URLs.
    """
    image_path = competitor_image
    
    if prompt_intelligence_service.is_url(competitor_image):
        image_path = await prompt_intelligence_service.download_image(competitor_image)
        if not image_path:
            raise HTTPException(status_code=400, detail="Failed to download competitor image from URL")
    elif not Path(competitor_image).exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {competitor_image}")
    
    from app.services.fal_seedream_service import FalSeedreamService
    
    logger.info(f"Starting end-to-end generation from competitor: {image_path}")
    
    prompt_result = await prompt_intelligence_service.generate_seedream_prompt(
        image_path, persona
    )
    
    if prompt_result.get("status") != "success":
        return {
            "status": "error",
            "error": "Failed to analyze competitor image",
            "details": prompt_result
        }
    
    generated_prompt = prompt_result.get("prompt", "")
    if not generated_prompt or generated_prompt.strip() == ", professional photography, 8K resolution, Canon EOS R5, 85mm f/1.4 lens, natural lighting, photorealistic, hyper-detailed skin texture":
        return {
            "status": "error",
            "error": "No usable content extracted from competitor image",
            "raw_analysis": prompt_result.get("raw_analysis", {})
        }
    
    logger.info(f"Generated prompt: {generated_prompt[:200]}...")
    
    fal_service = FalSeedreamService(persona)
    
    gen_result = await fal_service.generate_with_references(
        prompt=generated_prompt,
        aspect_ratio=aspect_ratio,
        output_dir=f"content/generated/{persona}",
        filename_prefix=f"{persona}_from_competitor",
        enable_safety_checker=False
    )
    
    return {
        "status": gen_result.get("status"),
        "source_image": competitor_image,
        "local_source_image": image_path,
        "generated_prompt": generated_prompt,
        "generated_image": gen_result.get("image_path"),
        "analysis": {
            "grok_vision": prompt_result.get("raw_analysis", {}).get("grok_vision"),
            "cogvlm": prompt_result.get("raw_analysis", {}).get("cogvlm"),
            "clip_interrogator": prompt_result.get("raw_analysis", {}).get("clip_interrogator")
        },
        "generation_details": gen_result
    }


@app.post("/api/prompt-intelligence/test-end-to-end")
async def test_end_to_end_generation(
    image_index: int = 1,
    persona: str = "starbright_monroe"
):
    """Test end-to-end workflow with ia_love2 research images"""
    image_paths = {
        1: "content/research_images/ia_love2/post_1.jpg",
        2: "content/research_images/ia_love2/post_2.jpg",
        3: "content/research_images/ia_love2/post_3.jpg"
    }
    
    image_path = image_paths.get(image_index)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Test image {image_index} not found")
    
    from app.services.fal_seedream_service import FalSeedreamService
    
    prompt_result = await prompt_intelligence_service.generate_seedream_prompt(image_path, persona)
    
    if prompt_result.get("status") != "success":
        return {"status": "error", "error": "Prompt generation failed", "details": prompt_result}
    
    generated_prompt = prompt_result.get("prompt", "")
    
    if len(generated_prompt) < 100:
        return {
            "status": "warning",
            "message": "Prompt may be insufficient - Replicate models may have timed out",
            "prompt": generated_prompt,
            "raw_analysis": prompt_result.get("raw_analysis", {}),
            "suggestion": "Retry with Grok Vision fallback by running the test again"
        }
    
    fal_service = FalSeedreamService(persona)
    
    gen_result = await fal_service.generate_with_references(
        prompt=generated_prompt,
        aspect_ratio="portrait_4_3",
        output_dir=f"content/generated/{persona}",
        filename_prefix=f"{persona}_e2e_test",
        enable_safety_checker=False
    )
    
    return {
        "status": gen_result.get("status"),
        "source_image": image_path,
        "prompt": generated_prompt,
        "generated_image": gen_result.get("image_path"),
        "generation_details": gen_result
    }



STATIC_DIR = Path("dist/public")
if STATIC_DIR.exists():
    @app.get("/dashboard/assets/{file_path:path}")
    async def serve_dashboard_assets(file_path: str):
        """Serve dashboard assets with no-cache headers"""
        from fastapi.responses import Response
        asset_path = STATIC_DIR / "assets" / file_path
        if asset_path.exists():
            content = asset_path.read_bytes()
            media_type = "application/javascript" if file_path.endswith(".js") else "text/css" if file_path.endswith(".css") else "application/octet-stream"
            return Response(
                content=content,
                media_type=media_type,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
            )
        raise HTTPException(status_code=404, detail="Asset not found")
    
    @app.get("/dashboard/favicon.png")
    async def dashboard_favicon():
        """Serve favicon for dashboard"""
        return FileResponse(STATIC_DIR / "favicon.png")
    
    @app.get("/dashboard")
    @app.get("/dashboard/")
    async def serve_dashboard():
        """Serve the React dashboard at /dashboard"""
        from fastapi.responses import Response
        content = (STATIC_DIR / "index.html").read_text()
        return Response(
            content=content,
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    
    @app.get("/dashboard/{full_path:path}")
    async def serve_dashboard_spa(full_path: str):
        """SPA fallback for dashboard routes"""
        from fastapi.responses import Response
        content = (STATIC_DIR / "index.html").read_text()
        return Response(
            content=content,
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
