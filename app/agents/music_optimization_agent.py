"""
Music Optimization Agent
Manages music library and uses AI to select optimal tracks for X posts based on trends.
"""
import os
import json
import subprocess
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

XAI_API_KEY = os.getenv("XAI_API_KEY")
MUSIC_LIBRARY_PATH = Path("content/music/library")
METADATA_PATH = Path("content/music/library_metadata.json")


class MusicOptimizationAgent:
    def __init__(self):
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Any]:
        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r") as f:
                return json.load(f)
        return {
            "tracks": [],
            "categories": {
                "mood": ["chill", "upbeat", "sensual", "dreamy", "energetic", "romantic", "mysterious"],
                "tempo": ["slow", "medium", "fast"],
                "genre": ["lofi", "pop", "rnb", "electronic", "ambient", "acoustic", "tropical"]
            },
            "trending_tags": []
        }
    
    def _save_metadata(self):
        with open(METADATA_PATH, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    def add_track(
        self,
        filename: str,
        title: str,
        mood: str = "chill",
        tempo: str = "medium",
        genre: str = "lofi",
        duration_seconds: int = 10,
        artist: str = "Unknown",
        royalty_free: bool = True
    ) -> Dict[str, Any]:
        track = {
            "id": f"track_{len(self.metadata['tracks']) + 1}",
            "filename": filename,
            "title": title,
            "mood": mood,
            "tempo": tempo,
            "genre": genre,
            "duration_seconds": duration_seconds,
            "artist": artist,
            "royalty_free": royalty_free,
            "use_count": 0,
            "added_date": datetime.now().isoformat()
        }
        self.metadata["tracks"].append(track)
        self._save_metadata()
        return track
    
    def list_tracks(self, mood: Optional[str] = None, genre: Optional[str] = None) -> List[Dict[str, Any]]:
        tracks = self.metadata["tracks"]
        if mood:
            tracks = [t for t in tracks if t.get("mood") == mood]
        if genre:
            tracks = [t for t in tracks if t.get("genre") == genre]
        return tracks
    
    def get_track_path(self, track_id: str) -> Optional[Path]:
        for track in self.metadata["tracks"]:
            if track["id"] == track_id:
                path = MUSIC_LIBRARY_PATH / track["filename"]
                if path.exists():
                    return path
        return None
    
    async def analyze_x_audio_trends(self) -> Dict[str, Any]:
        if not XAI_API_KEY:
            return {"error": "XAI_API_KEY not configured", "trends": []}
        
        prompt = """Analyze current audio/music trends on X (Twitter) for short-form video content, particularly for attractive female influencer content.

Focus on:
1. What types of background music are getting high engagement?
2. What moods/vibes are trending (chill, upbeat, sensual, etc.)?
3. What tempos work best for 5-10 second loops?
4. Any specific genres that are performing well?
5. What should be avoided?

Respond in JSON format:
{
    "trending_moods": ["mood1", "mood2"],
    "trending_genres": ["genre1", "genre2"],
    "recommended_tempo": "slow/medium/fast",
    "engagement_tips": ["tip1", "tip2"],
    "avoid": ["thing1", "thing2"],
    "summary": "Brief summary of what's working"
}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-1212",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"API error: {response.status_code}", "trends": []}
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    trends = json.loads(json_match.group())
                    self.metadata["trending_tags"] = trends.get("trending_moods", [])
                    self._save_metadata()
                    return {"success": True, "trends": trends}
                
                return {"success": True, "raw_response": content}
                
        except Exception as e:
            return {"error": str(e), "trends": []}
    
    async def recommend_music_for_caption(
        self,
        caption: Optional[str],
        video_filename: str = "",
        influencer: str = "starbright_monroe"
    ) -> Dict[str, Any]:
        """Recommend music based on caption text mood analysis"""
        available_tracks = self.list_tracks()
        if not available_tracks:
            return {
                "success": False,
                "error": "No tracks in library",
                "recommendation": None
            }
        
        # If no caption, fall back to video-based recommendation
        if not caption or not caption.strip():
            return await self.recommend_music_for_video(video_filename, influencer)
        
        # Use AI to analyze caption mood and match to tracks
        if not XAI_API_KEY:
            return self._caption_mood_fallback(caption, available_tracks)
        
        track_entries = []
        for t in available_tracks:
            track_entries.append(f"- {t['id']}: \"{t['title']}\" (mood: {t['mood']}, tempo: {t['tempo']}, genre: {t['genre']})")
        track_list = "\n".join(track_entries)
        
        prompt = f"""Analyze this social media caption and select the BEST matching background music track.

CAPTION:
"{caption}"

AVAILABLE TRACKS:
{track_list}

Consider:
1. The emotional tone of the caption (playful, sensual, mysterious, energetic, romantic, chill, dreamy)
2. Match the music mood to enhance the caption's vibe
3. For attractive female influencer content targeting male audience 20-60

Respond in JSON only:
{{
    "recommended_track_id": "track_X",
    "detected_mood": "the mood you detected in the caption",
    "reasoning": "Brief 1-sentence explanation of why this track matches",
    "confidence": 0.8
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-1212",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200
                    }
                )
                
                if response.status_code != 200:
                    return self._caption_mood_fallback(caption, available_tracks)
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    recommendation = json.loads(json_match.group())
                    track_id = recommendation.get("recommended_track_id")
                    track = next((t for t in available_tracks if t["id"] == track_id), None)
                    
                    if track:
                        return {
                            "success": True,
                            "recommendation": recommendation,
                            "track": track
                        }
                
                return self._caption_mood_fallback(caption, available_tracks)
                
        except Exception as e:
            return self._caption_mood_fallback(caption, available_tracks)
    
    def _caption_mood_fallback(self, caption: str, tracks: List[Dict]) -> Dict[str, Any]:
        """Fallback mood detection using keyword matching"""
        caption_lower = caption.lower()
        
        mood_keywords = {
            "sensual": ["sexy", "hot", "desire", "want", "touch", "feel", "intimate", "tempt", "tease"],
            "romantic": ["love", "heart", "sweet", "miss", "dream", "forever", "yours"],
            "mysterious": ["secret", "wonder", "curious", "mystery", "dark", "night", "shadow"],
            "energetic": ["energy", "fire", "power", "strong", "wild", "crazy", "dance"],
            "upbeat": ["happy", "fun", "smile", "laugh", "joy", "excited", "party", "vibe"],
            "dreamy": ["dream", "float", "soft", "gentle", "peace", "calm", "serene"],
            "chill": ["chill", "relax", "easy", "casual", "lazy", "cozy"]
        }
        
        detected_mood = "chill"  # default
        for mood, keywords in mood_keywords.items():
            if any(kw in caption_lower for kw in keywords):
                detected_mood = mood
                break
        
        # Find tracks matching the detected mood
        matching = [t for t in tracks if t.get("mood") == detected_mood]
        if not matching:
            matching = tracks  # fallback to all tracks
        
        import random
        selected = random.choice(matching)
        
        return {
            "success": True,
            "recommendation": {
                "recommended_track_id": selected["id"],
                "detected_mood": detected_mood,
                "reasoning": f"Matched '{detected_mood}' mood from caption keywords",
                "confidence": 0.7
            },
            "track": selected
        }
    
    async def recommend_music_for_video(
        self,
        video_filename: str,
        influencer: str = "starbright_monroe"
    ) -> Dict[str, Any]:
        context = self._extract_video_context(video_filename)
        
        if not XAI_API_KEY:
            return self._fallback_recommendation(context)
        
        available_tracks = self.list_tracks()
        if not available_tracks:
            return {
                "success": False,
                "error": "No tracks in library",
                "recommendation": None
            }
        
        track_list = "\n".join([
            f"- {t['id']}: {t['title']} (mood: {t['mood']}, tempo: {t['tempo']}, genre: {t['genre']})"
            for t in available_tracks
        ])
        
        prompt = f"""You are a social media optimization expert. Select the best background music for an X (Twitter) post.

VIDEO CONTEXT:
- Filename: {video_filename}
- Detected setting: {context.get('setting', 'unknown')}
- Detected outfit: {context.get('outfit', 'unknown')}
- Influencer: Starbright Monroe (attractive female influencer, male audience 20-60)

AVAILABLE TRACKS:
{track_list}

GOAL: Maximize engagement and reach on X. Consider current trends for short-form video content.

Respond in JSON:
{{
    "recommended_track_id": "track_X",
    "reasoning": "Brief explanation",
    "confidence": 0.0-1.0,
    "mood_match": "why this mood works",
    "alternative_track_id": "track_Y or null"
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-1212",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300
                    }
                )
                
                if response.status_code != 200:
                    return self._fallback_recommendation(context)
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    recommendation = json.loads(json_match.group())
                    track_id = recommendation.get("recommended_track_id")
                    track = next((t for t in available_tracks if t["id"] == track_id), None)
                    
                    return {
                        "success": True,
                        "recommendation": recommendation,
                        "track": track,
                        "context": context
                    }
                
                return self._fallback_recommendation(context)
                
        except Exception as e:
            return self._fallback_recommendation(context)
    
    def _extract_video_context(self, filename: str) -> Dict[str, str]:
        filename_lower = filename.lower()
        
        context = {"setting": "indoor", "outfit": "casual", "mood": "natural"}
        
        settings = {
            "beach": "beach", "pool": "poolside", "bedroom": "bedroom",
            "apartment": "apartment", "living": "living_room", "outdoor": "outdoor"
        }
        for key, value in settings.items():
            if key in filename_lower:
                context["setting"] = value
                break
        
        outfits = {
            "bikini": "bikini", "swimsuit": "swimsuit", "dress": "dress",
            "shorts": "shorts", "lingerie": "lingerie", "casual": "casual"
        }
        for key, value in outfits.items():
            if key in filename_lower:
                context["outfit"] = value
                break
        
        moods = {
            "sunset": "romantic", "golden": "warm", "morning": "fresh",
            "night": "mysterious", "playful": "playful"
        }
        for key, value in moods.items():
            if key in filename_lower:
                context["mood"] = value
                break
        
        return context
    
    def _fallback_recommendation(self, context: Dict[str, str]) -> Dict[str, Any]:
        tracks = self.list_tracks()
        if not tracks:
            return {"success": False, "error": "No tracks available", "recommendation": None}
        
        mood_map = {
            "beach": "chill",
            "poolside": "upbeat",
            "bedroom": "sensual",
            "apartment": "chill",
            "romantic": "romantic",
            "warm": "dreamy"
        }
        
        setting = context.get("setting", "indoor")
        mood = context.get("mood", "natural")
        preferred_mood = mood_map.get(setting, "chill")
        preferred_mood = mood_map.get(mood, preferred_mood)
        
        matching_tracks = [t for t in tracks if t.get("mood") == preferred_mood]
        if not matching_tracks:
            matching_tracks = tracks
        
        selected = matching_tracks[0]
        return {
            "success": True,
            "recommendation": {
                "recommended_track_id": selected["id"],
                "reasoning": f"Fallback selection based on {context.get('setting')} setting",
                "confidence": 0.6
            },
            "track": selected,
            "context": context,
            "fallback": True
        }


def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    audio_volume: float = 0.3,
    fade_out_duration: float = 1.0
) -> Dict[str, Any]:
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        video_info = json.loads(result.stdout)
        video_duration = float(video_info["format"]["duration"])
        
        fade_start = max(0, video_duration - fade_out_duration)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[1:a]volume={audio_volume},afade=t=out:st={fade_start}:d={fade_out_duration}[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        return {
            "success": True,
            "output_path": output_path,
            "video_duration": video_duration,
            "audio_volume": audio_volume
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


music_agent = MusicOptimizationAgent()
