"""
Instagram Reels-style Caption Templates for Luna Vale & Starbright Monroe
Two-part structure: Hook statement + Call-to-action with emoji
"""
import random
from typing import List, Dict

LUNA_CAPTION_TEMPLATES = [
    {
        "id": "reject_skinny",
        "lines": ["Men always reject me", "because they say", "I'm too skinny", "", "Can u say hi if you", "think I'm cute still 🥺"],
        "theme": "body_insecurity"
    },
    {
        "id": "crush_rejected",
        "lines": ["My crush rejected me", "because im too skinny", "", "Drop a ❤️ if you think", "i have a chance with you"],
        "theme": "dating"
    },
    {
        "id": "honest_opinion",
        "lines": ["Give me your honest", "opinion... I'm 18, 5'2", "and 90lbs", "", "Yay or nay?❤️"],
        "theme": "validation"
    },
    {
        "id": "too_small_date",
        "lines": ["Everyone says im", "too small to date", "", "Would you give me", "a chance? 👀"],
        "theme": "dating"
    },
    {
        "id": "built_like_pencil",
        "lines": ["Everyone loves thick", "girls and im over here", "built like a pencil", "", "Am I still cute tho?❤️"],
        "theme": "body_insecurity"
    },
    {
        "id": "invisible_girl",
        "lines": ["Im 5'2 and 90 pounds", "and always feel invisible", "", "Can you see me? 🙈"],
        "theme": "validation"
    },
    {
        "id": "skinny_dateable",
        "lines": ["Guys never notice me", "because im too small", "", "Drop a ❤️ if you think", "im still dateable"],
        "theme": "dating"
    },
    {
        "id": "swipe_right",
        "lines": ["I feel like the", "skinniest girl here", "", "Would you still", "swipe right on me? 🥹"],
        "theme": "dating"
    },
    {
        "id": "still_loading",
        "lines": ["Body type: still loading", "after 18 years lol", "", "Does anyone actually", "like girls this small? 😅"],
        "theme": "body_insecurity"
    },
    {
        "id": "friends_curves",
        "lines": ["All my friends have", "curves and im just... tiny", "", "Would you date me", "or just scroll? 👀"],
        "theme": "body_insecurity"
    },
    {
        "id": "look_twice",
        "lines": ["Would you look twice", "if you saw me like this", "", "Or just keep scrolling? 💭"],
        "theme": "validation"
    },
    {
        "id": "say_hi_pretty",
        "lines": ["Do you even notice", "girls built like me", "", "Say hi if you actually", "think im pretty 🥺"],
        "theme": "validation"
    },
    {
        "id": "bikini_skinny",
        "lines": ["Does this bikini even", "look good on someone", "this skinny?", "", "Be honest with me 🥹"],
        "theme": "body_insecurity"
    },
    {
        "id": "shorts_tiny",
        "lines": ["Trying to rock these", "shorts but im so tiny", "", "Do they work on me", "or nah? 👖💗"],
        "theme": "body_insecurity"
    },
    {
        "id": "summer_loading",
        "lines": ["This outfit says summer", "but my body says", "'still loading'", "", "Cute or too skinny? 😅"],
        "theme": "body_insecurity"
    },
    {
        "id": "gf_material",
        "lines": ["Am I girlfriend material", "or just the girl you", "scroll past?", "", "Be honest with me 💭"],
        "theme": "dating"
    },
    {
        "id": "rate_me",
        "lines": ["Rate me 1 to 10", "be brutally honest", "", "I can handle it 🥺"],
        "theme": "validation"
    },
    {
        "id": "date_or_scroll",
        "lines": ["Would you take me", "on a date or just", "double tap and leave?", "", "Tell me the truth 👀"],
        "theme": "dating"
    }
]


STARBRIGHT_CAPTION_TEMPLATES = [
    {
        "id": "caught_looking",
        "lines": ["Caught you looking 😉", "", "Don't be shy", "say hi"],
        "theme": "greeting"
    },
    {
        "id": "hey_you",
        "lines": ["Hey you 😌", "", "What caught your eye?"],
        "theme": "greeting"
    },
    {
        "id": "glad_stopped",
        "lines": ["Hi there", "glad you stopped by", "", "What's on your mind? 😊"],
        "theme": "greeting"
    },
    {
        "id": "share_moment",
        "lines": ["Just wanted to share", "this moment with you", "", "What are you up to? 😊"],
        "theme": "personal"
    },
    {
        "id": "thought_of_you",
        "lines": ["Thought of you", "when I took this", "", "Hope your day is good ✨"],
        "theme": "personal"
    },
    {
        "id": "my_afternoon",
        "lines": ["Spending my afternoon", "like this", "", "How about you? 🤍"],
        "theme": "personal"
    },
    {
        "id": "new_outfit",
        "lines": ["New outfit...", "thoughts?", "", "Be honest with me ✨"],
        "theme": "opinion"
    },
    {
        "id": "trying_new",
        "lines": ["Trying something new", "today", "", "What do you think? 😊"],
        "theme": "opinion"
    },
    {
        "id": "look_good",
        "lines": ["Does this look good?", "", "Tell me the truth 😌"],
        "theme": "opinion"
    },
    {
        "id": "feels_good",
        "lines": ["Something about today", "feels good", "", "Tell me about yours 🤍"],
        "theme": "warm"
    },
    {
        "id": "feeling_good",
        "lines": ["Feeling pretty good", "right now", "", "How are you doing? 😊"],
        "theme": "warm"
    },
    {
        "id": "nice_day",
        "lines": ["Having a nice day", "and wanted to share", "", "You too? ✨"],
        "theme": "warm"
    },
    {
        "id": "made_look",
        "lines": ["Made you look 😉", "", "Was it worth it?"],
        "theme": "playful"
    },
    {
        "id": "scrolled_back",
        "lines": ["You scrolled back", "didn't you", "", "I noticed 😌"],
        "theme": "playful"
    },
    {
        "id": "still_here",
        "lines": ["Still here?", "", "I like that about you 😊"],
        "theme": "playful"
    },
    {
        "id": "thanks_stopping",
        "lines": ["Thanks for", "stopping by", "", "Say something 😉"],
        "theme": "greeting"
    },
    {
        "id": "just_checking",
        "lines": ["Just checking in", "on you", "", "How's it going? 🤍"],
        "theme": "warm"
    },
    {
        "id": "like_this",
        "lines": ["You like this?", "", "Let me know 😊"],
        "theme": "opinion"
    }
]

def get_templates_for_influencer(influencer: str = "luna_vale") -> List[Dict]:
    """Get caption templates for specific influencer"""
    influencer_key = influencer.lower().replace("@", "").replace(" ", "_")
    if influencer_key in ["starbright_monroe", "starbright"]:
        return STARBRIGHT_CAPTION_TEMPLATES
    return LUNA_CAPTION_TEMPLATES

def get_random_caption(influencer: str = "luna_vale") -> Dict:
    """Get a random caption template for influencer"""
    templates = get_templates_for_influencer(influencer)
    return random.choice(templates)


def get_random_captions(count: int = 5, influencer: str = "luna_vale") -> List[Dict]:
    """Get multiple random captions without duplicates for influencer"""
    templates = get_templates_for_influencer(influencer)
    if count >= len(templates):
        return templates.copy()
    return random.sample(templates, count)


def get_captions_by_theme(theme: str, influencer: str = "luna_vale") -> List[Dict]:
    """Get captions filtered by theme for influencer"""
    templates = get_templates_for_influencer(influencer)
    return [c for c in templates if c["theme"] == theme]


def get_all_themes(influencer: str = "luna_vale") -> List[str]:
    """Get list of all available themes for influencer"""
    templates = get_templates_for_influencer(influencer)
    return list(set(c["theme"] for c in templates))


def format_caption_for_display(caption: Dict) -> str:
    """Format caption lines for display in textarea"""
    return "\n".join(caption["lines"])
