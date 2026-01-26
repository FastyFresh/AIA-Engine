"""
Content Admin Routes - Categorize and manage Telegram content
"""
import os
import shutil
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/content", tags=["content"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
CONTENT_BASE = "content/telegram"
PERSONAS = ["starbright", "luna"]
TIERS = ["unsorted", "teaser", "companion", "vip", "archive"]

def verify_admin(api_key: str):
    if not ADMIN_API_KEY or api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def ensure_dirs():
    for persona in PERSONAS:
        for tier in TIERS:
            os.makedirs(f"{CONTENT_BASE}/{persona}/{tier}", exist_ok=True)

ensure_dirs()

class MoveRequest(BaseModel):
    filename: str
    from_tier: str
    to_tier: str
    persona: str = "starbright"

class BulkMoveRequest(BaseModel):
    files: List[str]
    from_tier: str
    to_tier: str
    persona: str = "starbright"

@router.get("/list/{persona}/{tier}")
async def list_content(persona: str, tier: str, x_api_key: str = Header(None), page: int = 1, per_page: int = 24):
    verify_admin(x_api_key)
    
    if persona not in PERSONAS:
        raise HTTPException(status_code=400, detail="Invalid persona")
    if tier not in TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    path = f"{CONTENT_BASE}/{persona}/{tier}"
    if not os.path.exists(path):
        return {"files": [], "count": 0, "page": 1, "total_pages": 0}
    
    all_files = []
    for f in os.listdir(path):
        filepath = f"{path}/{f}"
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            ext = os.path.splitext(f)[1].lower()
            all_files.append({
                "name": f,
                "size": stat.st_size,
                "type": "video" if ext in [".mp4", ".mov", ".webm"] else "image",
                "path": f"/api/content/file/{persona}/{tier}/{f}"
            })
    
    all_files.sort(key=lambda x: x["name"])
    total = len(all_files)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    
    return {"files": all_files[start:end], "count": total, "page": page, "total_pages": total_pages}

@router.get("/file/{persona}/{tier}/{filename}")
async def get_file(persona: str, tier: str, filename: str, x_api_key: str = Header(None), key: str = None):
    api_key = x_api_key or key
    verify_admin(api_key)
    
    filepath = f"{CONTENT_BASE}/{persona}/{tier}/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(filepath)

@router.post("/move")
async def move_content(req: MoveRequest, x_api_key: str = Header(None)):
    verify_admin(x_api_key)
    
    if req.from_tier not in TIERS or req.to_tier not in TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    src = f"{CONTENT_BASE}/{req.persona}/{req.from_tier}/{req.filename}"
    dst = f"{CONTENT_BASE}/{req.persona}/{req.to_tier}/{req.filename}"
    
    if not os.path.exists(src):
        raise HTTPException(status_code=404, detail="File not found")
    
    shutil.move(src, dst)
    return {"success": True, "message": f"Moved to {req.to_tier}"}

@router.post("/bulk-move")
async def bulk_move(req: BulkMoveRequest, x_api_key: str = Header(None)):
    verify_admin(x_api_key)
    
    moved = 0
    errors = []
    
    for filename in req.files:
        src = f"{CONTENT_BASE}/{req.persona}/{req.from_tier}/{filename}"
        dst = f"{CONTENT_BASE}/{req.persona}/{req.to_tier}/{filename}"
        
        try:
            if os.path.exists(src):
                shutil.move(src, dst)
                moved += 1
            else:
                errors.append(f"{filename}: not found")
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
    
    return {"moved": moved, "errors": errors}

@router.get("/stats/{persona}")
async def get_stats(persona: str, x_api_key: str = Header(None)):
    verify_admin(x_api_key)
    
    stats = {}
    for tier in TIERS:
        path = f"{CONTENT_BASE}/{persona}/{tier}"
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if os.path.isfile(f"{path}/{f}")]
            stats[tier] = len(files)
        else:
            stats[tier] = 0
    
    return stats

@router.get("/admin", response_class=HTMLResponse)
async def content_admin_page():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Manager - Telegram</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div id="app" class="p-6 max-w-7xl mx-auto">
        <div id="login" class="max-w-md mx-auto mt-20">
            <div class="glass rounded-xl p-8 border border-white/10">
                <h1 class="text-2xl font-bold mb-6 text-center">Content Manager</h1>
                <input type="password" id="apiKey" placeholder="Enter Admin API Key" 
                    class="w-full p-3 rounded-lg bg-gray-800 border border-gray-700 mb-4">
                <button onclick="login()" class="w-full py-3 bg-pink-500 hover:bg-pink-600 rounded-lg font-semibold">
                    Access
                </button>
            </div>
        </div>
        <div id="manager" class="hidden">
            <div class="flex items-center justify-between mb-6">
                <h1 class="text-2xl font-bold">Content Manager</h1>
                <div class="flex gap-2">
                    <select id="persona" onchange="loadContent()" class="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2">
                        <option value="starbright">Starbright</option>
                        <option value="luna">Luna</option>
                    </select>
                    <a href="/dashboard" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">Dashboard</a>
                </div>
            </div>
            <div id="tierButtons" class="flex gap-2 mb-6 flex-wrap"></div>
            <div id="stats" class="mb-4 text-sm text-gray-400"></div>
            <div id="content" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4"></div>
            <div id="viewer" class="hidden fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
                <div class="max-w-2xl w-full">
                    <div id="viewerContent" class="mb-4"></div>
                    <div id="viewerActions" class="flex flex-wrap gap-2 justify-center"></div>
                    <button onclick="closeViewer()" class="mt-4 px-6 py-2 bg-gray-700 rounded-lg mx-auto block">Close</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        let apiKey = localStorage.getItem('adminApiKey') || '';
        let currentTier = 'unsorted';
        let files = [];
        let currentIndex = 0;
        let currentPage = 1;
        let totalPages = 1;
        let totalCount = 0;
        const tiers = ['unsorted', 'teaser', 'companion', 'vip', 'archive'];
        const tierLabels = {unsorted:'Unsorted', teaser:'Teaser (Free)', companion:'Companion ($9.99)', vip:'VIP ($24.99)', archive:'Archive'};
        const tierColors = {unsorted:'gray', teaser:'blue', companion:'purple', vip:'yellow', archive:'red'};

        function login() {
            apiKey = document.getElementById('apiKey').value;
            localStorage.setItem('adminApiKey', apiKey);
            init();
        }

        async function init() {
            if (!apiKey) return;
            document.getElementById('login').classList.add('hidden');
            document.getElementById('manager').classList.remove('hidden');
            renderTierButtons();
            await loadContent();
        }

        function renderTierButtons() {
            const container = document.getElementById('tierButtons');
            container.innerHTML = tiers.map(t => `
                <button onclick="selectTier('${t}')" id="tier-${t}"
                    class="px-4 py-2 rounded-lg border transition ${currentTier === t ? 'bg-pink-500 border-pink-500' : 'bg-gray-800 border-gray-700 hover:border-gray-500'}">
                    ${tierLabels[t]} <span id="count-${t}" class="ml-1 text-xs opacity-70"></span>
                </button>
            `).join('');
        }

        async function selectTier(tier) {
            currentTier = tier;
            currentPage = 1;
            renderTierButtons();
            await loadContent();
        }

        async function loadContent() {
            const persona = document.getElementById('persona').value;
            try {
                const statsRes = await fetch(`/api/content/stats/${persona}`, {headers: {'x-api-key': apiKey}});
                const stats = await statsRes.json();
                tiers.forEach(t => {
                    const el = document.getElementById(`count-${t}`);
                    if (el) el.textContent = `(${stats[t] || 0})`;
                });

                const res = await fetch(`/api/content/list/${persona}/${currentTier}?page=${currentPage}`, {headers: {'x-api-key': apiKey}});
                const data = await res.json();
                files = data.files || [];
                totalPages = data.total_pages || 1;
                totalCount = data.count || 0;
                renderContent();
            } catch (e) {
                console.error(e);
            }
        }
        
        function goToPage(page) {
            currentPage = Math.max(1, Math.min(page, totalPages));
            loadContent();
        }

        function renderContent() {
            const container = document.getElementById('content');
            if (files.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-20 text-gray-500">No content in this tier</div>';
                document.getElementById('stats').innerHTML = '';
                return;
            }
            container.innerHTML = files.map((f, i) => `
                <div onclick="openViewer(${i})" class="aspect-square bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-pink-500 relative">
                    ${f.type === 'video' 
                        ? `<video src="${f.path}?key=${apiKey}" class="w-full h-full object-cover"></video>
                           <div class="absolute top-2 right-2 bg-black/50 px-2 py-1 rounded text-xs">VIDEO</div>`
                        : `<img src="${f.path}?key=${apiKey}" class="w-full h-full object-cover">`
                    }
                </div>
            `).join('');
            
            document.getElementById('stats').innerHTML = totalPages > 1 ? `
                <div class="flex items-center justify-between">
                    <span>Showing ${files.length} of ${totalCount} items</span>
                    <div class="flex gap-2 items-center">
                        <button onclick="goToPage(1)" class="px-3 py-1 bg-gray-800 rounded ${currentPage === 1 ? 'opacity-50' : 'hover:bg-gray-700'}" ${currentPage === 1 ? 'disabled' : ''}>First</button>
                        <button onclick="goToPage(${currentPage - 1})" class="px-3 py-1 bg-gray-800 rounded ${currentPage === 1 ? 'opacity-50' : 'hover:bg-gray-700'}" ${currentPage === 1 ? 'disabled' : ''}>Prev</button>
                        <span class="px-3">Page ${currentPage} of ${totalPages}</span>
                        <button onclick="goToPage(${currentPage + 1})" class="px-3 py-1 bg-gray-800 rounded ${currentPage === totalPages ? 'opacity-50' : 'hover:bg-gray-700'}" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        <button onclick="goToPage(${totalPages})" class="px-3 py-1 bg-gray-800 rounded ${currentPage === totalPages ? 'opacity-50' : 'hover:bg-gray-700'}" ${currentPage === totalPages ? 'disabled' : ''}>Last</button>
                    </div>
                </div>
            ` : `<span>Showing ${totalCount} items</span>`;
        }

        function openViewer(index) {
            currentIndex = index;
            const f = files[index];
            const viewer = document.getElementById('viewer');
            const content = document.getElementById('viewerContent');
            const actions = document.getElementById('viewerActions');
            
            content.innerHTML = f.type === 'video'
                ? `<video src="${f.path}?key=${apiKey}" controls class="max-h-[60vh] mx-auto rounded-lg"></video>`
                : `<img src="${f.path}?key=${apiKey}" class="max-h-[60vh] mx-auto rounded-lg">`;
            
            actions.innerHTML = tiers.filter(t => t !== currentTier).map(t => `
                <button onclick="moveFile('${t}')" class="px-4 py-2 rounded-lg ${t === 'archive' ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-700 hover:bg-gray-600'}">
                    ${t === 'archive' ? 'Delete' : '→ ' + tierLabels[t]}
                </button>
            `).join('') + `
                <button onclick="nextFile(-1)" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">← Prev</button>
                <button onclick="nextFile(1)" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">Next →</button>
            `;
            
            viewer.classList.remove('hidden');
        }

        function closeViewer() {
            document.getElementById('viewer').classList.add('hidden');
        }

        function nextFile(dir) {
            currentIndex = (currentIndex + dir + files.length) % files.length;
            openViewer(currentIndex);
        }

        async function moveFile(toTier) {
            const persona = document.getElementById('persona').value;
            const f = files[currentIndex];
            try {
                await fetch('/api/content/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'x-api-key': apiKey},
                    body: JSON.stringify({filename: f.name, from_tier: currentTier, to_tier: toTier, persona})
                });
                files.splice(currentIndex, 1);
                if (files.length === 0) {
                    closeViewer();
                } else if (currentIndex >= files.length) {
                    currentIndex = files.length - 1;
                    openViewer(currentIndex);
                } else {
                    openViewer(currentIndex);
                }
                renderContent();
                loadContent();
            } catch (e) {
                console.error(e);
            }
        }

        if (apiKey) init();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
