"""Twitter/X API integration routes."""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twitter", tags=["Twitter"])

from app.agents.twitter_oauth2_agent import TwitterOAuth2Agent
from app.agents.music_optimization_agent import music_agent, merge_audio_video

twitter_oauth2_agent = TwitterOAuth2Agent()


@router.get("/status")
async def twitter_status():
    """Get Twitter OAuth 2.0 connection status"""
    return twitter_oauth2_agent.get_status()


@router.get("/auth")
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
        <h1>Twitter Authorization</h1>
        <div class="box">
            <p>Click the button below to authorize this app to post on your behalf:</p>
            <p><a href="{result['auth_url']}" target="_blank">Authorize with Twitter</a></p>
        </div>
        <div class="box">
            <p><strong>After authorizing:</strong></p>
            <p>You'll be redirected to a callback URL. The authorization will complete automatically.</p>
        </div>
    </body>
    </html>
    """)


@router.get("/callback")
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
            <h1>Authorization Failed</h1>
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
        <h1>Authorization Successful!</h1>
        <div class="success">
            <p>Connected as: <strong>@{username}</strong></p>
            <p>The app can now post tweets on your behalf.</p>
            <p><a href="/api/twitter/test">Test posting</a> | <a href="/dashboard">Back to Dashboard</a></p>
        </div>
    </body>
    </html>
    """)


@router.get("/test")
async def twitter_test_post():
    """Test Twitter posting with a simple tweet"""
    result = await twitter_oauth2_agent.post_text("Test post from AIA Engine! #AIInfluencer")
    return result


@router.post("/post")
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


@router.post("/post_full")
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


@router.get("/compose")
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


@router.get("/disconnect")
async def twitter_disconnect():
    """Disconnect Twitter authorization"""
    return twitter_oauth2_agent.disconnect()
