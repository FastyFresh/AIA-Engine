"""Web Chat API routes - DM-style chat for website"""
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["webchat"])


class StartChatRequest(BaseModel):
    persona_id: str = "starbright_monroe"
    visitor_id: str


class SendMessageRequest(BaseModel):
    persona_id: str = "starbright_monroe"
    visitor_id: str
    message: str


@router.post("/start")
async def start_chat(request: StartChatRequest) -> dict:
    """Start a new DM conversation - returns the 'brb' message"""
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    
    session = await telegram_db.get_or_create_webchat_session(
        request.visitor_id, request.persona_id
    )
    
    brb_messages = {
        "starbright_monroe": "hold on a sec, let me finish something real quick 💕",
        "luna_vale": "one moment love, just finishing up here ✨"
    }
    
    brb = brb_messages.get(request.persona_id, "one sec, be right back!")
    
    return {
        "status": "started",
        "message": brb,
        "delay_seconds": 60,
        "session_id": f"{request.persona_id}:{request.visitor_id}"
    }


@router.post("/ready")
async def mark_ready(request: StartChatRequest) -> dict:
    """Called after the delay - marks session as ready for real conversation"""
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    await telegram_db.set_webchat_ready(request.visitor_id, request.persona_id)
    
    greetings = {
        "starbright_monroe": "hey! sorry about that, was just getting out of the shower lol 😊 what's up?",
        "luna_vale": "hi babe! sorry, was doing my makeup 💄 how are you?"
    }
    
    greeting = greetings.get(request.persona_id, "hey! I'm here now, what's up?")
    
    await telegram_db.add_webchat_message(
        request.visitor_id, request.persona_id, "assistant", greeting
    )
    
    return {
        "status": "ready",
        "message": greeting,
        "typing_duration": 3
    }


@router.post("/send")
async def send_message(request: SendMessageRequest) -> dict:
    """Send a message and get AI response"""
    from app.telegram.conversation_engine import ConversationEngine
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    
    session = await telegram_db.get_or_create_webchat_session(
        request.visitor_id, request.persona_id
    )
    
    if not session.get("ready"):
        return {
            "message": "just a sec, almost there! 💕",
            "typing_duration": 2
        }
    
    await telegram_db.add_webchat_message(
        request.visitor_id, request.persona_id, "user", request.message
    )
    
    history = await telegram_db.get_webchat_history(
        request.visitor_id, request.persona_id, limit=20
    )
    
    history_formatted = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    
    engine = ConversationEngine(request.persona_id)
    
    extra_context = """You are chatting through DMs on your personal website - NOT a bot or AI.
Never mention being a bot, AI, or automated. You are the real person.
Keep responses casual and short like real DMs (1-3 sentences usually).
Build connection and trust. Be warm, friendly, flirty when appropriate.
If the conversation gets too spicy/NSFW, naturally suggest: 'haha you're wild 😏 if you wanna see more you should check out my dfans, link's in my bio'
Never break character. You ARE this person chatting from your phone."""
    
    response = await engine.generate_response(
        user_message=request.message,
        conversation_history=history_formatted,
        user_name="babe",
        subscription_tier="free",
        extra_context=extra_context
    )
    
    await telegram_db.add_webchat_message(
        request.visitor_id, request.persona_id, "assistant", response
    )
    
    typing_duration = min(max(len(response) * 0.05, 2), 8)
    
    return {
        "message": response,
        "typing_duration": int(typing_duration)
    }


@router.get("/history/{persona_id}/{visitor_id}")
async def get_history(persona_id: str, visitor_id: str) -> dict:
    """Get chat history for a session"""
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    
    session = await telegram_db.get_or_create_webchat_session(visitor_id, persona_id)
    history = await telegram_db.get_webchat_history(visitor_id, persona_id)
    
    return {
        "messages": history,
        "ready": bool(session.get("ready"))
    }


@router.get("/test", response_class=HTMLResponse)
async def chat_test_page():
    """Test page for the DM chat feature"""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DM Starbright - Test</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 400px;
        }
        .profile-card {
            background: #fff;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b9d, #c44569);
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 50px;
        }
        .name { font-size: 24px; font-weight: 600; color: #1a1a2e; }
        .bio { color: #666; margin: 10px 0 20px; font-size: 14px; }
        .dm-btn {
            background: linear-gradient(45deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .dm-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(255,107,157,0.4);
        }
        .chat-window {
            display: none;
            background: #fff;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            height: 500px;
            flex-direction: column;
        }
        .chat-header {
            background: linear-gradient(45deg, #ff6b9d, #c44569);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        .chat-name { font-weight: 600; }
        .chat-status { font-size: 12px; opacity: 0.9; }
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f5f5f5;
        }
        .message {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 18px;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.4;
        }
        .message.them {
            background: white;
            border-bottom-left-radius: 5px;
            margin-right: auto;
        }
        .message.me {
            background: linear-gradient(45deg, #ff6b9d, #c44569);
            color: white;
            border-bottom-right-radius: 5px;
            margin-left: auto;
        }
        .typing {
            display: none;
            color: #999;
            font-size: 12px;
            padding: 5px 0;
        }
        .typing.visible { display: block; }
        .typing-dots {
            display: inline-flex;
            gap: 3px;
        }
        .typing-dots span {
            width: 6px;
            height: 6px;
            background: #999;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        .chat-input {
            display: flex;
            padding: 15px;
            background: white;
            border-top: 1px solid #eee;
            gap: 10px;
        }
        .chat-input input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 10px 15px;
            font-size: 14px;
            outline: none;
        }
        .chat-input input:focus { border-color: #ff6b9d; }
        .chat-input button {
            background: linear-gradient(45deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
        }
        .waiting-overlay {
            display: none;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.95);
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 20px;
        }
        .waiting-overlay.visible { display: flex; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #ff6b9d;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .countdown { font-size: 24px; font-weight: 600; color: #1a1a2e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="profile-card" id="profileCard">
            <div class="avatar">⭐</div>
            <div class="name">Starbright Monroe</div>
            <div class="bio">19 • ☕ barista by day • ✨ dreamer by night<br>link in bio for the spicy stuff 🌶️</div>
            <button class="dm-btn" onclick="startChat()">DM me 💬</button>
        </div>
        
        <div class="chat-window" id="chatWindow" style="position: relative;">
            <div class="chat-header">
                <div class="chat-avatar">⭐</div>
                <div>
                    <div class="chat-name">Starbright</div>
                    <div class="chat-status" id="chatStatus">Active now</div>
                </div>
            </div>
            <div class="messages" id="messages"></div>
            <div class="typing" id="typing">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                Starbright is typing...
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Message..." onkeypress="if(event.key==='Enter')sendMessage()">
                <button onclick="sendMessage()">➤</button>
            </div>
            <div class="waiting-overlay" id="waitingOverlay">
                <div class="spinner"></div>
                <div class="countdown" id="countdown">60</div>
                <div style="color:#666;">She'll be right back...</div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/api/chat';
        const PERSONA = 'starbright_monroe';
        let visitorId = localStorage.getItem('visitor_id') || 'visitor_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('visitor_id', visitorId);
        let chatReady = false;

        function addMessage(text, isMe) {
            const messages = document.getElementById('messages');
            const msg = document.createElement('div');
            msg.className = 'message ' + (isMe ? 'me' : 'them');
            msg.textContent = text;
            messages.appendChild(msg);
            messages.scrollTop = messages.scrollHeight;
        }

        function showTyping(show) {
            document.getElementById('typing').classList.toggle('visible', show);
        }

        async function startChat() {
            document.getElementById('profileCard').style.display = 'none';
            document.getElementById('chatWindow').style.display = 'flex';
            document.getElementById('waitingOverlay').classList.add('visible');

            try {
                const res = await fetch(API_BASE + '/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({persona_id: PERSONA, visitor_id: visitorId})
                });
                const data = await res.json();
                
                addMessage(data.message, false);
                
                let seconds = data.delay_seconds || 60;
                const countdownEl = document.getElementById('countdown');
                const interval = setInterval(() => {
                    seconds--;
                    countdownEl.textContent = seconds;
                    if (seconds <= 0) {
                        clearInterval(interval);
                        markReady();
                    }
                }, 1000);
            } catch (err) {
                console.error('Start chat error:', err);
                addMessage('Sorry, something went wrong. Try again?', false);
                document.getElementById('waitingOverlay').classList.remove('visible');
            }
        }

        async function markReady() {
            try {
                const res = await fetch(API_BASE + '/ready', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({persona_id: PERSONA, visitor_id: visitorId})
                });
                const data = await res.json();
                
                document.getElementById('waitingOverlay').classList.remove('visible');
                chatReady = true;
                
                showTyping(true);
                setTimeout(() => {
                    showTyping(false);
                    addMessage(data.message, false);
                }, (data.typing_duration || 3) * 1000);
            } catch (err) {
                console.error('Mark ready error:', err);
                document.getElementById('waitingOverlay').classList.remove('visible');
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (!text || !chatReady) return;
            
            input.value = '';
            addMessage(text, true);
            showTyping(true);

            try {
                const res = await fetch(API_BASE + '/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({persona_id: PERSONA, visitor_id: visitorId, message: text})
                });
                const data = await res.json();
                
                setTimeout(() => {
                    showTyping(false);
                    addMessage(data.message, false);
                }, (data.typing_duration || 2) * 1000);
            } catch (err) {
                console.error('Send message error:', err);
                showTyping(false);
                addMessage('oops something glitched, try again?', false);
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
