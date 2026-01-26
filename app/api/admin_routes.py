"""Admin routes for bot activity dashboard"""
import os
from html import escape

from fastapi import APIRouter, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

router = APIRouter(tags=["admin"])

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def verify_admin_key(x_admin_key: str = Header(None), x_api_key: str = Header(None)):
    """Verify admin API key for protected endpoints"""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin API not configured")
    api_key = x_admin_key or x_api_key
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True


@router.get("/admin")
async def admin_login_page():
    """Admin login page with secure form"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-box { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 40px; width: 100%; max-width: 400px; }
            h1 { text-align: center; margin-bottom: 30px; background: linear-gradient(90deg, #f093fb, #f5576c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #888; }
            input[type="password"] { width: 100%; padding: 12px 16px; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; background: rgba(0,0,0,0.3); color: #fff; font-size: 16px; }
            input[type="password"]:focus { outline: none; border-color: #f093fb; }
            button { width: 100%; padding: 14px; background: linear-gradient(90deg, #f093fb, #f5576c); border: none; border-radius: 8px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; }
            button:hover { opacity: 0.9; }
            .error { color: #f5576c; text-align: center; margin-top: 15px; display: none; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>Bot Activity Dashboard</h1>
            <form id="loginForm">
                <div class="form-group">
                    <label>Admin Key</label>
                    <input type="password" id="adminKey" placeholder="Enter your admin key" required>
                </div>
                <button type="submit">Access Dashboard</button>
                <p class="error" id="errorMsg">Invalid admin key</p>
            </form>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const key = document.getElementById('adminKey').value;
                const response = await fetch('/admin/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-Admin-Key': key }
                });
                if (response.ok) {
                    sessionStorage.setItem('adminKey', key);
                    window.location.href = '/admin/stats';
                } else {
                    document.getElementById('errorMsg').style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """)


@router.post("/admin/verify")
async def verify_admin(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    """Verify admin key via POST"""
    if not ADMIN_API_KEY or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return {"status": "ok"}


@router.get("/admin/stats")
async def stats_dashboard(x_admin_key: str = Header(None), key: str = None):
    """Visual stats dashboard (requires admin key via header or URL)"""
    admin_key = x_admin_key or key
    if not ADMIN_API_KEY or admin_key != ADMIN_API_KEY:
        return HTMLResponse("""
        <script>
            const key = sessionStorage.getItem('adminKey');
            if (key) {
                fetch('/admin/stats', { headers: { 'X-Admin-Key': key } })
                    .then(r => r.text())
                    .then(html => { document.open(); document.write(html); document.close(); })
                    .catch(() => window.location.href = '/admin');
            } else {
                window.location.href = '/admin';
            }
        </script>
        """)
    
    from app.telegram.user_database import db as telegram_db
    await telegram_db.init_db()
    
    stats = {}
    convos = {}
    for persona_id in ["starbright_monroe", "luna_vale"]:
        stats[persona_id] = await telegram_db.get_user_stats(persona_id)
        convos[persona_id] = await telegram_db.get_recent_conversations(persona_id, limit=30)
    
    sb = stats.get("starbright_monroe", {})
    luna = stats.get("luna_vale", {})
    
    def format_conversations(messages, persona_name):
        if not messages:
            return "<p style='color:#666;text-align:center;padding:20px;'>No conversations yet</p>"
        html_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = escape(msg.get('content', '')[:200])
            if len(msg.get('content', '')) > 200:
                content += "..."
            name = escape(msg.get('first_name') or 'Unknown')
            tier = msg.get('subscription_tier', 'free')
            tier_color = {'free': '#888', 'companion': '#4ecdc4', 'vip': '#f5576c'}.get(tier, '#888')
            time_str = msg.get('created_at', '')[:16].replace('T', ' ')
            
            if role == 'user':
                html_parts.append(f'''
                    <div class="msg user-msg">
                        <div class="msg-header"><span class="user-name">{name}</span> <span class="tier" style="color:{tier_color}">[{tier}]</span> <span class="time">{time_str}</span></div>
                        <div class="msg-content">{content}</div>
                    </div>
                ''')
            else:
                html_parts.append(f'''
                    <div class="msg bot-msg">
                        <div class="msg-header"><span class="bot-name">{persona_name}</span> <span class="time">{time_str}</span></div>
                        <div class="msg-content">{content}</div>
                    </div>
                ''')
        return ''.join(html_parts)
    
    sb_convos = format_conversations(convos.get("starbright_monroe", []), "Starbright")
    luna_convos = format_conversations(convos.get("luna_vale", []), "Luna")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Activity Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; min-height: 100vh; padding: 40px 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            h1 {{ text-align: center; margin-bottom: 40px; background: linear-gradient(90deg, #f093fb, #f5576c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; }}
            .card h2 {{ font-size: 18px; margin-bottom: 16px; color: #f093fb; }}
            .stat {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
            .stat:last-child {{ border: none; }}
            .stat-label {{ color: #888; }}
            .stat-value {{ font-weight: 600; font-size: 20px; }}
            .stat-value.free {{ color: #888; }}
            .stat-value.companion {{ color: #4ecdc4; }}
            .stat-value.vip {{ color: #f5576c; }}
            .totals {{ background: linear-gradient(135deg, rgba(240,147,251,0.2), rgba(245,87,108,0.2)); border-radius: 16px; padding: 24px; text-align: center; }}
            .totals h2 {{ margin-bottom: 20px; }}
            .total-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .total-item {{ padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px; }}
            .total-number {{ font-size: 36px; font-weight: 700; }}
            .total-label {{ color: #888; margin-top: 8px; }}
            .refresh {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            .convo-section {{ margin-top: 40px; }}
            .convo-section h2 {{ margin-bottom: 20px; color: #f093fb; }}
            .convo-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            .convo-tab {{ padding: 10px 20px; background: rgba(255,255,255,0.05); border-radius: 8px; cursor: pointer; border: none; color: #fff; }}
            .convo-tab.active {{ background: rgba(240,147,251,0.3); }}
            .convo-panel {{ display: none; background: rgba(255,255,255,0.03); border-radius: 12px; max-height: 500px; overflow-y: auto; }}
            .convo-panel.active {{ display: block; }}
            .msg {{ padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .msg:last-child {{ border: none; }}
            .msg-header {{ font-size: 12px; margin-bottom: 6px; display: flex; gap: 8px; align-items: center; }}
            .user-name {{ color: #4ecdc4; font-weight: 600; }}
            .bot-name {{ color: #f5576c; font-weight: 600; }}
            .tier {{ font-size: 11px; }}
            .time {{ color: #555; margin-left: auto; }}
            .msg-content {{ color: #ccc; line-height: 1.5; }}
            .user-msg {{ background: rgba(78,205,196,0.05); }}
            .bot-msg {{ background: rgba(245,87,108,0.05); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Bot Activity Dashboard</h1>
            
            <div class="totals">
                <h2>Overall</h2>
                <div class="total-grid">
                    <div class="total-item">
                        <div class="total-number">{sb.get('total_users', 0) + luna.get('total_users', 0)}</div>
                        <div class="total-label">Total Users</div>
                    </div>
                    <div class="total-item">
                        <div class="total-number" style="color: #4ecdc4;">{sb.get('companion_users', 0) + luna.get('companion_users', 0) + sb.get('vip_users', 0) + luna.get('vip_users', 0)}</div>
                        <div class="total-label">Paying Subscribers</div>
                    </div>
                </div>
            </div>
            
            <div class="cards" style="margin-top: 30px;">
                <div class="card">
                    <h2>Starbright Monroe</h2>
                    <div class="stat">
                        <span class="stat-label">Total Users</span>
                        <span class="stat-value">{sb.get('total_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Free</span>
                        <span class="stat-value free">{sb.get('free_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Companion ($9.99)</span>
                        <span class="stat-value companion">{sb.get('companion_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">VIP ($24.99)</span>
                        <span class="stat-value vip">{sb.get('vip_users', 0)}</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Luna Vale</h2>
                    <div class="stat">
                        <span class="stat-label">Total Users</span>
                        <span class="stat-value">{luna.get('total_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Free</span>
                        <span class="stat-value free">{luna.get('free_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Companion ($9.99)</span>
                        <span class="stat-value companion">{luna.get('companion_users', 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">VIP ($24.99)</span>
                        <span class="stat-value vip">{luna.get('vip_users', 0)}</span>
                    </div>
                </div>
            </div>
            
            <div class="convo-section">
                <h2>Recent Conversations</h2>
                <div class="convo-tabs">
                    <button class="convo-tab active" onclick="showTab('sb')">Starbright</button>
                    <button class="convo-tab" onclick="showTab('luna')">Luna</button>
                </div>
                <div id="sb-panel" class="convo-panel active">
                    {sb_convos}
                </div>
                <div id="luna-panel" class="convo-panel">
                    {luna_convos}
                </div>
            </div>
            
            <p class="refresh">Refresh page to update stats</p>
        </div>
        <script>
            function showTab(tab) {{
                document.querySelectorAll('.convo-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.convo-panel').forEach(p => p.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(tab + '-panel').classList.add('active');
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
