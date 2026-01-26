"""
AI Conversation Engine for Telegram Bots
Supports multiple providers: OpenRouter (Dolphin), Grok (xAI), and Replicate
"""
import os
import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .bot_config import PERSONA_SYSTEM_PROMPTS

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    role: str
    content: str

class ConversationEngine:
    """Handles AI-powered conversations with persona consistency"""
    
    def __init__(self, persona_id: str, provider: str = "openrouter"):
        self.persona_id = persona_id
        self.system_prompt = PERSONA_SYSTEM_PROMPTS.get(persona_id, "")
        self.xai_key = os.getenv("XAI_API_KEY", "")
        self.replicate_key = os.getenv("REPLICATE_API_TOKEN", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.provider = provider
        
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[ConversationMessage] = None,
        user_name: str = "",
        subscription_tier: str = "free",
        extra_context: str = ""
    ) -> str:
        """Generate a persona-authentic response to the user's message"""
        
        if self.provider == "openrouter":
            return await self._generate_openrouter(
                user_message, conversation_history or [], user_name, subscription_tier, extra_context
            )
        elif self.provider == "replicate":
            return await self._generate_replicate(
                user_message, conversation_history or [], user_name, subscription_tier
            )
        else:
            response = await self._generate_grok(
                user_message, conversation_history or [], user_name, subscription_tier, extra_context
            )
            if response.startswith("Hmm, my thoughts"):
                logger.info("Grok failed, falling back to OpenRouter")
                return await self._generate_openrouter(
                    user_message, conversation_history or [], user_name, subscription_tier, extra_context
                )
            return response
    
    async def _generate_openrouter(
        self,
        user_message: str,
        history: List[ConversationMessage],
        user_name: str,
        tier: str,
        extra_context: str = ""
    ) -> str:
        """Generate response using OpenRouter API with Dolphin (uncensored)"""
        if not self.openrouter_key:
            logger.error("OPENROUTER_API_KEY not configured")
            return "I'm having a moment... try again?"
        
        messages = self._build_messages(user_message, history, user_name, tier, extra_context)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://replit.com",
                        "X-Title": "AIA Engine"
                    },
                    json={
                        "model": "venice/uncensored:free",
                        "messages": messages,
                        "max_tokens": 300,
                        "temperature": 0.85
                    },
                    timeout=45.0
                )
                response.raise_for_status()
                data = response.json()
                
                ai_response = data["choices"][0]["message"]["content"]
                return self._post_process_response(ai_response)
                
        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout, falling back to Grok")
            return await self._generate_grok(user_message, history, user_name, tier)
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}, falling back to Grok")
            return await self._generate_grok(user_message, history, user_name, tier)
    
    async def _generate_grok(
        self,
        user_message: str,
        history: List[ConversationMessage],
        user_name: str,
        tier: str,
        extra_context: str = ""
    ) -> str:
        """Generate response using Grok API"""
        if not self.xai_key:
            logger.error("XAI_API_KEY not configured")
            return "Hmm, my thoughts got jumbled. Try again?"
        
        messages = self._build_messages(user_message, history, user_name, tier, extra_context)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3",
                        "messages": messages,
                        "max_tokens": 300,
                        "temperature": 0.85
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                ai_response = data["choices"][0]["message"]["content"]
                return self._post_process_response(ai_response)
                
        except httpx.TimeoutException:
            logger.error("Grok API timeout")
            return "Hmm, my thoughts got jumbled. Try again?"
        except Exception as e:
            logger.error(f"Grok API error: {e}")
            return "Hmm, my thoughts got jumbled. Try again?"
    
    async def _generate_replicate(
        self,
        user_message: str,
        history: List[ConversationMessage],
        user_name: str,
        tier: str
    ) -> str:
        """Generate response using Dolphin 2.9 Llama 3 70B (uncensored)"""
        if not self.replicate_key:
            logger.error("REPLICATE_API_TOKEN not configured")
            return "I'm having a moment... try again? 💭"
        
        system_prompt = self._build_system_prompt(user_name, tier)
        user_prompt = self._build_user_prompt(user_message, history)
        
        try:
            async with httpx.AsyncClient() as client:
                create_response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Bearer {self.replicate_key}",
                        "Content-Type": "application/json",
                        "Prefer": "wait"
                    },
                    json={
                        "version": "ee173688d3b8d9e05a5b910f10fb9bab1e9348963ab224579bb90d9fce3fb00b",
                        "input": {
                            "prompt": user_prompt,
                            "system_prompt": system_prompt,
                            "max_tokens": 300,
                            "temperature": 0.85,
                            "repetition_penalty": 1.1
                        }
                    },
                    timeout=60.0
                )
                result = create_response.json()
                logger.info(f"Replicate response status: {create_response.status_code}, body: {result}")
                create_response.raise_for_status()
                
                if result.get("status") == "succeeded":
                    output = result.get("output", [])
                    if isinstance(output, list):
                        output = "".join(output)
                    return self._post_process_response(output)
                elif result.get("status") == "failed":
                    logger.error(f"Replicate prediction failed: {result.get('error')}")
                    return "Sorry, I got distracted for a sec... what were you saying?"
                else:
                    prediction_id = result.get("id")
                    for _ in range(30):
                        await asyncio.sleep(1)
                        status_response = await client.get(
                            f"https://api.replicate.com/v1/predictions/{prediction_id}",
                            headers={"Authorization": f"Bearer {self.replicate_key}"},
                            timeout=10.0
                        )
                        status_data = status_response.json()
                        
                        if status_data.get("status") == "succeeded":
                            output = status_data.get("output", [])
                            if isinstance(output, list):
                                output = "".join(output)
                            return self._post_process_response(output)
                        elif status_data.get("status") == "failed":
                            logger.error(f"Replicate prediction failed: {status_data.get('error')}")
                            return "Sorry, I got distracted for a sec... what were you saying?"
                    
                    logger.error("Replicate prediction timeout")
                    return "Sorry, I got distracted for a sec... what were you saying?"
                
        except Exception as e:
            logger.error(f"Replicate API error: {e}")
            return "I'm having a moment... try again? 💭"
    
    def _build_messages(
        self,
        user_message: str,
        history: List[ConversationMessage],
        user_name: str,
        tier: str,
        extra_context: str = ""
    ) -> List[Dict[str, str]]:
        """Build the message array for OpenAI-compatible APIs"""
        
        enhanced_system = self.system_prompt
        if user_name:
            enhanced_system += f"\n\nThe person you're talking to is named {user_name}. IMPORTANT: Do NOT use their name in every message. Only use it occasionally (every 5-10 messages max) to keep it natural."
        
        if tier == "vip":
            enhanced_system += "\n\nThis is a VIP subscriber - be extra warm, personal, and open to intimate conversation."
        elif tier == "companion":
            enhanced_system += "\n\nThis is a Companion subscriber - show appreciation for their support and be more flirtatious."
        
        if extra_context:
            enhanced_system += f"\n\n{extra_context}"
        
        messages = [{"role": "system", "content": enhanced_system}]
        
        for msg in history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _build_system_prompt(self, user_name: str, tier: str) -> str:
        """Build the system prompt for Dolphin model"""
        enhanced_system = self.system_prompt
        if user_name:
            enhanced_system += f"\n\nThe person you're talking to is named {user_name}. IMPORTANT: Do NOT use their name in every message. Only use it occasionally (every 5-10 messages max) to keep it natural."
        
        if tier == "vip":
            enhanced_system += "\n\nThis is a VIP subscriber - be extra warm, personal, and open to intimate conversation."
        elif tier == "companion":
            enhanced_system += "\n\nThis is a Companion subscriber - show appreciation for their support and be more flirtatious."
        
        enhanced_system += "\n\nNever mention 'SYSTEM MESSAGE' or break character."
        
        return enhanced_system
    
    def _build_user_prompt(self, user_message: str, history: List[ConversationMessage]) -> str:
        """Build the user prompt including conversation history"""
        prompt_parts = []
        
        for msg in history[-6:]:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            else:
                prompt_parts.append(f"You: {msg.content}")
        
        prompt_parts.append(f"User: {user_message}")
        
        return "\n".join(prompt_parts)
    
    def _post_process_response(self, response: str) -> str:
        """Clean up the AI response"""
        response = response.strip()
        
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        
        if len(response) > 500:
            sentences = response.split('. ')
            truncated = '. '.join(sentences[:3])
            if not truncated.endswith('.'):
                truncated += '.'
            response = truncated
        
        return response
