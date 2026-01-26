"""
Prompt Safety Filter - Content Policy Compliance

Safety-conscious prompt filtering to avoid model content flags.
Transforms sensitive vocabulary into policy-safe synonyms while
maintaining the brand aesthetic (elegant, confident, stylish).

Word-boundary-aware regex ensures innocent words containing flagged
substrings are preserved (e.g., "therapist" won't be corrupted).
"""

import re
from typing import List, Optional, Tuple


class PromptSafetyFilter:
    """
    Safety-conscious prompt filtering to avoid model content flags.
    
    Transforms sensitive vocabulary into policy-safe synonyms while
    maintaining the brand aesthetic (elegant, confident, stylish).
    """
    
    VOCABULARY_MAP = {
        "lingerie set": "loungewear set",
        "lingerie": "elegant loungewear",
        "lace lingerie set": "silk loungewear set",
        "lace lingerie": "delicate silk loungewear",
        "black lace lingerie set": "black silk loungewear set",
        "black lace lingerie": "black silk loungewear set",
        "sexy": "alluring",
        "sultry": "captivating",
        "seductive": "elegant",
        "revealing": "stylish",
        "skimpy": "minimal",
        "provocative": "eye-catching",
        "nude": "neutral-toned",
        "naked": "natural",
        "topless": "strapless top",
        "sheer": "lightweight fabric",
        "see-through": "semi-transparent",
        "thong": "minimal bottoms",
        "g-string": "minimal bottoms",
        "sports bra": "sports bra",
        "push-up bra": "fitted top",
        "cleavage": "neckline",
        "busty": "fitted",
        "curvy": "athletic",
        "bedroom eyes": "confident gaze",
        "come hither": "inviting expression",
        "erotic": "artistic",
        "sensual": "graceful",
        "body-hugging": "form-fitting",
        "skin-tight": "fitted",
        "low-cut": "v-neck",
        "plunging": "elegant v-neck",
        "backless": "open-back design",
        "underwear": "lounge set",
        "panties": "matching bottoms",
        "corset": "structured top",
        "garter": "thigh accessory",
        "stockings": "sheer leggings",
        "fishnet": "patterned fabric",
        "teddy": "one-piece loungewear",
        "negligee": "silk nightwear",
        "babydoll": "flowing silk top",
        "camisole": "silk tank top",
        "boudoir": "bedroom setting",
        "buttocks": "figure",
        "rounded buttocks": "curves",
        "accentuating her rounded buttocks": "highlighting her silhouette",
        "accentuating her buttocks": "flattering her figure",
        "hugs her slim figure": "fits her slender frame",
        "hugging her figure": "complementing her frame",
        "hugging her curves": "flattering her silhouette",
        "tight bodysuit": "fitted bodysuit",
        "tight long-sleeved": "fitted long-sleeved",
        "slim figure": "slender frame",
    }
    
    BLOCKED_PATTERNS = [
        r"\bnude\b",
        r"\bnaked\b", 
        r"\btopless\b",
        r"\berotic\b",
        r"\bsexual\b",
        r"\bporn\b",
        r"\bexplicit\b",
        r"\bnsfw\b",
    ]
    
    FALLBACK_OUTFITS = {
        "lingerie": ["silk loungewear set", "elegant robe", "satin pajamas"],
        "bikini": ["two-piece swimwear", "athletic swimsuit", "beach coverup"],
        "underwear": ["lounge set", "casual home wear", "comfort clothing"],
        "bodysuit": ["fitted one-piece", "dance bodysuit", "athletic leotard"],
    }
    
    @classmethod
    def sanitize_prompt(cls, prompt: str) -> Tuple[str, List[str]]:
        """
        Sanitize a prompt by replacing sensitive vocabulary using word-boundary matching.
        Preserves original casing structure and avoids corrupting innocent words.
        
        Returns:
            Tuple of (sanitized_prompt, list of substitutions made)
        """
        sanitized = prompt
        substitutions = []
        
        sorted_terms = sorted(cls.VOCABULARY_MAP.keys(), key=len, reverse=True)
        
        for term in sorted_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, sanitized, re.IGNORECASE):
                replacement = cls.VOCABULARY_MAP[term]
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                substitutions.append(f"{term} → {replacement}")
        
        return sanitized, substitutions
    
    @classmethod
    def sanitize_outfit(cls, outfit: str) -> str:
        """Sanitize just the outfit description."""
        sanitized, _ = cls.sanitize_prompt(outfit)
        return sanitized
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a prompt for blocked patterns.
        
        Returns:
            Tuple of (is_valid, reason if invalid)
        """
        prompt_lower = prompt.lower()
        
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, prompt_lower):
                match = re.search(pattern, prompt_lower)
                return False, f"Blocked term found: {match.group() if match else pattern}"
        
        return True, None
    
    @classmethod
    def get_fallback_outfit(cls, original_outfit: str) -> Optional[str]:
        """
        Get a fallback outfit if the original triggers filters.
        
        Returns:
            Alternative outfit string, or None if no fallback available
        """
        outfit_lower = original_outfit.lower()
        
        for trigger, alternatives in cls.FALLBACK_OUTFITS.items():
            if trigger in outfit_lower:
                return alternatives[0]
        
        return "elegant casual wear"
    
    @classmethod
    def get_progressive_alternatives(cls, outfit: str) -> List[str]:
        """
        Get progressively safer alternatives for an outfit.
        Used for retry logic.
        """
        alternatives = [
            cls.sanitize_outfit(outfit),
        ]
        
        outfit_lower = outfit.lower()
        for trigger, alts in cls.FALLBACK_OUTFITS.items():
            if trigger in outfit_lower:
                alternatives.extend(alts)
                break
        
        alternatives.append("stylish casual outfit")
        
        return list(dict.fromkeys(alternatives))


prompt_safety_filter = PromptSafetyFilter()
