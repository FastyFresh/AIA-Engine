from typing import Any, Dict, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import os
import time

logger = logging.getLogger(__name__)

LLMProvider = Literal["anthropic", "openai", "grok"]

LLM_TIMEOUT_SECONDS = 10
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_RESET_SECONDS = 300


@dataclass
class LLMResponse:
    success: bool
    content: str
    provider: str
    latency_ms: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    fallback_used: bool = False


@dataclass 
class CircuitBreaker:
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    is_open: bool = False
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.now()
        if self.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
            self.is_open = True
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def record_success(self):
        self.failure_count = 0
        self.is_open = False
    
    def should_allow_request(self) -> bool:
        if not self.is_open:
            return True
        if self.last_failure and datetime.now() - self.last_failure > timedelta(seconds=CIRCUIT_BREAKER_RESET_SECONDS):
            logger.info("Circuit breaker RESET after cooldown")
            self.is_open = False
            self.failure_count = 0
            return True
        return False


@dataclass
class PromptConfig:
    system_prompt: str
    user_prompt: str
    max_tokens: int = 500
    temperature: float = 0.7


class LLMClient:
    
    DEFAULT_PROVIDER: LLMProvider = "anthropic"
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {
            "anthropic": CircuitBreaker(),
            "openai": CircuitBreaker(),
            "grok": CircuitBreaker(),
        }
        self._clients_initialized = False
        self._anthropic_client = None
        self._openai_client = None
    
    def _init_clients(self):
        if self._clients_initialized:
            return
        
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        self._clients_initialized = True
    
    def _get_available_provider(self, preferred: Optional[LLMProvider] = None) -> Optional[LLMProvider]:
        providers_to_try = []
        
        if preferred:
            providers_to_try.append(preferred)
        
        providers_to_try.extend([p for p in ["anthropic", "openai", "grok"] if p != preferred])
        
        for provider in providers_to_try:
            if self._is_provider_available(provider) and self._circuit_breakers[provider].should_allow_request():
                return provider
        
        return None
    
    def _is_provider_available(self, provider: LLMProvider) -> bool:
        if provider == "anthropic":
            return self._anthropic_client is not None
        elif provider == "openai":
            return self._openai_client is not None
        elif provider == "grok":
            return os.environ.get("XAI_API_KEY") is not None
        return False
    
    async def generate_text(
        self,
        prompt_config: PromptConfig,
        provider: Optional[LLMProvider] = None,
        fallback_text: Optional[str] = None
    ) -> LLMResponse:
        self._init_clients()
        
        preferred = provider or self.DEFAULT_PROVIDER
        providers_to_try = [preferred] + [p for p in ["anthropic", "openai", "grok"] if p != preferred]
        
        last_error = None
        total_start_time = time.time()
        
        for current_provider in providers_to_try:
            if not self._is_provider_available(current_provider):
                continue
            if not self._circuit_breakers[current_provider].should_allow_request():
                logger.info(f"Skipping {current_provider}: circuit breaker open")
                continue
            
            start_time = time.time()
            
            try:
                content = await asyncio.wait_for(
                    self._call_provider(current_provider, prompt_config),
                    timeout=LLM_TIMEOUT_SECONDS
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                self._circuit_breakers[current_provider].record_success()
                
                logger.info(
                    f"LLM response: provider={current_provider}, "
                    f"latency={latency_ms:.0f}ms, chars={len(content)}"
                )
                
                return LLMResponse(
                    success=True,
                    content=content,
                    provider=current_provider,
                    latency_ms=latency_ms,
                    fallback_used=(current_provider != preferred)
                )
                
            except asyncio.TimeoutError:
                latency_ms = (time.time() - start_time) * 1000
                self._circuit_breakers[current_provider].record_failure()
                last_error = f"Timeout on {current_provider}"
                logger.warning(f"LLM timeout after {latency_ms:.0f}ms on {current_provider}, trying next...")
                continue
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self._circuit_breakers[current_provider].record_failure()
                last_error = str(e)
                logger.warning(f"LLM error on {current_provider}: {e}, trying next...")
                continue
        
        total_latency = (time.time() - total_start_time) * 1000
        logger.warning(f"All LLM providers failed, using fallback text")
        
        return LLMResponse(
            success=False,
            content=fallback_text or "",
            provider="none",
            latency_ms=total_latency,
            error=last_error or "No provider available",
            fallback_used=True
        )
    
    async def _call_provider(self, provider: LLMProvider, config: PromptConfig) -> str:
        if provider == "anthropic":
            return await self._call_anthropic(config)
        elif provider == "openai":
            return await self._call_openai(config)
        elif provider == "grok":
            return await self._call_grok(config)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_anthropic(self, config: PromptConfig) -> str:
        if not self._anthropic_client:
            raise RuntimeError("Anthropic client not initialized")
        
        client = self._anthropic_client
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=config.max_tokens,
                system=config.system_prompt,
                messages=[
                    {"role": "user", "content": config.user_prompt}
                ]
            )
        )
        
        content_block = response.content[0]
        if hasattr(content_block, 'text'):
            return content_block.text
        return str(content_block)
    
    async def _call_openai(self, config: PromptConfig) -> str:
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        client = self._openai_client
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": config.user_prompt}
                ]
            )
        )
        
        content = response.choices[0].message.content
        return content if content else ""
    
    async def _call_grok(self, config: PromptConfig) -> str:
        import httpx
        
        xai_key = os.environ.get("XAI_API_KEY")
        if not xai_key:
            raise RuntimeError("XAI_API_KEY not set")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {xai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-2-latest",
                    "messages": [
                        {"role": "system", "content": config.system_prompt},
                        {"role": "user", "content": config.user_prompt}
                    ],
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature
                },
                timeout=LLM_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_status(self) -> Dict[str, Any]:
        self._init_clients()
        
        return {
            "providers": {
                "anthropic": {
                    "available": self._is_provider_available("anthropic"),
                    "circuit_open": self._circuit_breakers["anthropic"].is_open,
                    "failure_count": self._circuit_breakers["anthropic"].failure_count
                },
                "openai": {
                    "available": self._is_provider_available("openai"),
                    "circuit_open": self._circuit_breakers["openai"].is_open,
                    "failure_count": self._circuit_breakers["openai"].failure_count
                },
                "grok": {
                    "available": self._is_provider_available("grok"),
                    "circuit_open": self._circuit_breakers["grok"].is_open,
                    "failure_count": self._circuit_breakers["grok"].failure_count
                }
            },
            "default_provider": self.DEFAULT_PROVIDER,
            "timeout_seconds": LLM_TIMEOUT_SECONDS,
            "circuit_breaker_threshold": CIRCUIT_BREAKER_THRESHOLD
        }
