import uuid
import time
import shutil
import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from logging.handlers import RotatingFileHandler

# 引入本地模块
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from mailer import send_contact_info_email
from models import FarmerCreate, BuyerCreate

# ==========================================
# 1. 核心配置与日志
# ==========================================
# ✅ 关键修复：显式定义所有数据文件路径 (钉死在根目录)
BASE_DIR = os.getcwd()
DB_USERS = os.path.join(BASE_DIR, "users.json")
DB_FARMERS = os.path.join(BASE_DIR, "farmers.json")
DB_BUYERS = os.path.join(BASE_DIR, "buyers.json")
DB_PROPOSALS = os.path.join(BASE_DIR, "proposals.json")
DB_NOTIFS = os.path.join(BASE_DIR, "notifications.json")
DB_REFS = os.path.join(BASE_DIR, "references.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# 日志配置
logger = logging.getLogger("cattle_app")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler("app.log", maxBytes=1024*1024, backupCount=1)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

ACCESS_TOKEN_EXPIRE_MINUTES = 60
app = FastAPI(title="Cattle Match System (Fixed Paths)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        print(error_msg)
        return JSONResponse(status_code=500, content={"detail": "Server Error"})

# ==========================================
# 2. 统一数据读写工具 (Helper)
# ==========================================
# 彻底替代 db.py，防止路径混淆
def load_json(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def append_record(filepath, record):
    data = load_json(filepath)
    data.append(record)
    save_json(filepath, data)

# 通知助手
def save_notification(user_id, title, details=None):
    notif = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": title,
        "details": details or {},
        "timestamp": time.time(),
        "read": False
    }
    append_record(DB_NOTIFS, notif)

# 简单匹配逻辑 (替代 matcher.py 以防路径问题)
def simple_match(new_record, target_file, is_farmer):
    targets = load_json(target_file)
    count = 0
    for t in targets:
        # 简单匹配：同品种 + 状态开放
        if t.get('race') == new_record.get('race') and t.get('status', 'OPEN') == 'OPEN':
            count += 1
            # 给对方发通知
            target_user = t.get('owner_id')
            if target_user:
                role = "Farmer" if is_farmer else "Buyer"
                save_notification(target_user, f"New Match: {role} posted {new_record.get('race')}", new_record)
    return count

# ==========================================
# 3. 依赖与模型
# ==========================================
def get_current_admin(current_user: str = Depends(get_current_user)):
    users = load_json(DB_USERS)
    user = next((u for u in users if u['username'] == current_user), None)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin required")
    return user

class UserRegister(BaseModel):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str
    phone: str
    address: str
    tax_id: Optional[str] = None
    ie: Optional[str] = None
    role: Optional[str] = "user"

class Proposal(BaseModel):
    supply_id: str
    price_offer: float
    message: Optional[str] = ""

class CustomCity(BaseModel):
    state: str
    name: str

# ==========================================
# 4. Auth 接口
# ==========================================
@app.post("/auth/register")
def register(user: UserRegister):
    users = load_json(DB_USERS)
    if any(u['username'] == user.username for u in users):
        raise HTTPException(status_code=400, detail="Username taken")

    new_user = user.dict()
    new_user['password'] = get_password_hash(user.password)
    new_user['created_at'] = time.time()
    new_user['is_active'] = True

    append_record(DB_USERS, new_user)
    return {"msg": "Created"}

@app.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_json(DB_USERS)
    user = next((u for u in users if u['username'] == form_data.username), None)

    if not user or not verify_password(form_data.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account disabled")

    token = create_access_token(data={"sub": user['username']}, expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer", "role": user.get("role", "user"), "username": user['username']}

# ==========================================
# 5. 文件与基础接口
# ==========================================
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user: str = Depends(get_current_user)):
    ext = file.filename.split(".")[-1]
    name = f"{uuid.uuid4()}.{ext}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as b:
        shutil.copyfileobj(file.file, b)
    return {"filename": name}

@app.get("/api/files/{filename}")
def get_file(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path): raise HTTPException(404)
    return FileResponse(path)

@app.get("/api/market")
def get_market():
    # 市场只看 Supply (Farmers)
    farmers = load_json(DB_FARMERS)
    active = [f for f in farmers if f.get('status', 'OPEN') == 'OPEN']
    active.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return {"supply": active}

# ==========================================
# 6. 用户业务接口 (Listings)
# ==========================================
@app.post("/api/farmer")
def create_farmer(data: FarmerCreate, user: str = Depends(get_current_user)):
    rec = data.dict()
    rec.update({"id": str(uuid.uuid4()), "timestamp": time.time(), "owner_id": user, "status": "OPEN"})
    append_record(DB_FARMERS, rec)
    # 简单的匹配通知
    count = simple_match(rec, DB_BUYERS, True)
    return {"id": rec['id'], "matches": count}

@app.post("/api/buyer")
def create_buyer(data: BuyerCreate, user: str = Depends(get_current_user)):
    rec = data.dict()
    rec.update({"id": str(uuid.uuid4()), "timestamp": time.time(), "owner_id": user})
    append_record(DB_BUYERS, rec)
    count = simple_match(rec, DB_FARMERS, False)
    return {"id": rec['id'], "matches": count}

@app.get("/api/my-listings")
def get_my_listings(user: str = Depends(get_current_user)):
    farmers = load_json(DB_FARMERS)
    buyers = load_json(DB_BUYERS)
    return {
        "supply": sorted([f for f in farmers if f.get('owner_id') == user], key=lambda x: x.get('timestamp', 0), reverse=True),
        "demand": sorted([b for b in buyers if b.get('owner_id') == user], key=lambda x: x.get('timestamp', 0), reverse=True)
    }

@app.get("/api/notifications")
def get_notifs(user: str = Depends(get_current_user)):
    notifs = load_json(DB_NOTIFS)
    return sorted([n for n in notifs if n['user_id'] == user], key=lambda x: x.get('timestamp', 0), reverse=True)

# ==========================================
# 7. 提案与交易 (Proposals) - 修复重点
# ==========================================
@app.post("/api/proposals")
def create_proposal(prop: Proposal, user: str = Depends(get_current_user)):
    # 检查 Supply
    farmers = load_json(DB_FARMERS)
    supply = next((f for f in farmers if f['id'] == prop.supply_id), None)

    if not supply: raise HTTPException(404, "Supply not found")
    if supply.get('status') != 'OPEN': raise HTTPException(400, "Listing not open")

    # 检查用户角色
    users = load_json(DB_USERS)
    u_data = next((u for u in users if u['username'] == user), {})
    if u_data.get('role') == 'farmer': raise HTTPException(400, "Farmers cannot buy")

    new_prop = {
        "id": str(uuid.uuid4()),
        "supply_id": prop.supply_id,
        "buyer_id": user,
        "buyer_contact": u_data.get('phone', 'Unknown'),
        "price_offer": prop.price_offer,
        "message": prop.message,
        "status": "PENDING",
        "timestamp": time.time()
    }

    append_record(DB_PROPOSALS, new_prop)

    # 给 Farmer 发通知
    save_notification(supply['owner_id'], f"New Offer: R$ {prop.price_offer}", new_prop)

    return {"msg": "Sent", "id": new_prop['id']}

@app.get("/api/my-proposals")
def get_received_proposals(user: str = Depends(get_current_user)):
    # 我是 Farmer，查看发给我的提案
    farmers = load_json(DB_FARMERS)
    proposals = load_json(DB_PROPOSALS)

    my_supply_ids = [f['id'] for f in farmers if f.get('owner_id') == user]
    received = [p for p in proposals if p['supply_id'] in my_supply_ids]

    return sorted(received, key=lambda x: x.get('timestamp', 0), reverse=True)

@app.get("/api/my-sent-proposals")
def get_sent_proposals(user: str = Depends(get_current_user)):
    # 我是 Buyer，查看我发出的
    proposals = load_json(DB_PROPOSALS)
    farmers = load_json(DB_FARMERS)

    sent = [p for p in proposals if p['buyer_id'] == user]

    # 填充详情
    for p in sent:
        supply = next((f for f in farmers if f['id'] == p['supply_id']), None)
        if supply:
            p['supply_detail'] = {
                "race": supply.get('race'),
                "qty": supply.get('quantity'),
                "location": f"{supply.get('city')}, {supply.get('state')}",
                "photo": supply.get('cattle_photo')
            }

    return sorted(sent, key=lambda x: x.get('timestamp', 0), reverse=True)

@app.post("/api/proposals/{pid}/{action}")
def handle_proposal(pid: str, action: str, user: str = Depends(get_current_user)):
    proposals = load_json(DB_PROPOSALS)
    prop = next((p for p in proposals if p['id'] == pid), None)
    if not prop: raise HTTPException(404, "Not found")

    if action == 'reject':
        prop['status'] = 'REJECTED'
    elif action == 'accept':
        prop['status'] = 'ACCEPTED'
        # 锁定 Supply
        farmers = load_json(DB_FARMERS)
        supply = next((f for f in farmers if f['id'] == prop['supply_id']), None)
        if supply:
            supply['status'] = 'AWAITING_PAYMENT'
            supply['buyer_id'] = prop['buyer_id']
            save_json(DB_FARMERS, farmers) # 保存状态

            # 通知买家
            save_notification(prop['buyer_id'], "Offer Accepted! Pay fee to lock.", prop)

    save_json(DB_PROPOSALS, proposals)
    return {"msg": "Updated"}

@app.post("/api/pay-reservation/{pid}")
def pay_fee(pid: str, user: str = Depends(get_current_user)):
    proposals = load_json(DB_PROPOSALS)
    prop = next((p for p in proposals if p['id'] == pid), None)

    if not prop or prop['buyer_id'] != user: raise HTTPException(403)

    farmers = load_json(DB_FARMERS)
    supply = next((f for f in farmers if f['id'] == prop['supply_id']), None)

    if not supply: raise HTTPException(404)

    # 状态流转
    supply['status'] = 'SOLD'
    prop['status'] = 'PAID'

    save_json(DB_FARMERS, farmers)
    save_json(DB_PROPOSALS, proposals)

    # 通知卖家
    save_notification(supply['owner_id'], "Deal Closed! Buyer paid fee.", prop)

    return {"msg": "Paid", "nfe": supply.get('nfe_file'), "gta": supply.get('gta_file')}

# ==========================================
# 8. Admin & System
# ==========================================
def get_refs():
    if not os.path.exists(DB_REFS):
        save_json(DB_REFS, {"breeds": ["Nelore", "Angus"], "custom_cities": []})
    return load_json(DB_REFS)

@app.get("/api/system/references")
def sys_refs(): return get_refs()

@app.post("/api/admin/breed")
def add_breed(name: str, admin: dict = Depends(get_current_admin)):
    refs = get_refs()
    if name not in refs["breeds"]:
        refs["breeds"].append(name)
        refs["breeds"].sort()
        save_json(DB_REFS, refs)
    return {"msg": "Added"}

@app.delete("/api/admin/breed/{name}")
def del_breed(name: str, admin: dict = Depends(get_current_admin)):
    refs = get_refs()
    refs["breeds"] = [b for b in refs["breeds"] if b != name]
    save_json(DB_REFS, refs)
    return {"msg": "Deleted"}

@app.post("/api/admin/location/city")
def add_city(city: CustomCity, admin: dict = Depends(get_current_admin)):
    refs = get_refs()
    refs['custom_cities'].append(city.dict())
    save_json(DB_REFS, refs)
    return {"msg": "Added"}

@app.delete("/api/admin/location/city/{s}/{n}")
def del_city(s: str, n: str, admin: dict = Depends(get_current_admin)):
    refs = get_refs()
    refs['custom_cities'] = [c for c in refs['custom_cities'] if not (c['state'] == s and c['name'] == n)]
    save_json(DB_REFS, refs)
    return {"msg": "Deleted"}

@app.get("/api/admin/stats")
def admin_stats(admin: dict = Depends(get_current_admin)):
    return {
        "total_users": len(load_json(DB_USERS)),
        "total_supply": len(load_json(DB_FARMERS)),
        "total_demand": len(load_json(DB_BUYERS)),
        "recent_activity": [] # 简化
    }

@app.get("/api/admin/users")
def admin_users(admin: dict = Depends(get_current_admin)):
    return [{k:v for k,v in u.items() if k!='password'} for u in load_json(DB_USERS)]

@app.patch("/api/admin/user/{username}/toggle-status")
def toggle_status(username: str, admin: dict = Depends(get_current_admin)):
    users = load_json(DB_USERS)
    for u in users:
        if u['username'] == username:
            u['is_active'] = not u.get('is_active', True)
            save_json(DB_USERS, users)
            return {"msg": "Toggled"}
    raise HTTPException(404)

@app.delete("/api/admin/user/{username}")
def del_user(username: str, admin: dict = Depends(get_current_admin)):
    users = load_json(DB_USERS)
    users = [u for u in users if u['username'] != username]
    save_json(DB_USERS, users)
    return {"msg": "Deleted"}

@app.get("/api/admin/listings")
def admin_list(admin: dict = Depends(get_current_admin)):
    return {"supply": load_json(DB_FARMERS), "demand": load_json(DB_BUYERS)}

@app.delete("/api/admin/listing/{ltype}/{lid}")
def del_listing(ltype: str, lid: str, admin: dict = Depends(get_current_admin)):
    fname = DB_FARMERS if ltype == 'supply' else DB_BUYERS
    data = load_json(fname)
    data = [i for i in data if i['id'] != lid]
    save_json(fname, data)
    return {"msg": "Deleted"}

@app.get("/api/admin/logs")
def admin_logs(admin: dict = Depends(get_current_admin)):
    if os.path.exists("app.log"):
        with open("app.log", "r") as f: return {"logs": f.readlines()[-100:]}
    return {"logs": []}

@app.delete("/api/admin/logs")
def clear_logs(admin: dict = Depends(get_current_admin)):
    open("app.log", "w").close()
    return {"msg": "Cleared"}