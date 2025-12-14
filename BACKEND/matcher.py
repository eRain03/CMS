import time
from typing import Dict
from db import db
# ✅ 引入邮件模块
from mailer import send_match_email

def save_notification(user_id: str, title: str, details: Dict):
    """保存站内信"""
    notif = {
        "user_id": user_id,
        "message": title,
        "details": details,
        "timestamp": time.time(),
        "read": False
    }
    db.add_record("notifications.json", notif)
    print(f"🔔 Notification saved for {user_id}")

def check_match(farmer: Dict, buyer: Dict) -> bool:
    # 1. 地理位置匹配
    # Buyer targets: [{'state': 'PA', 'city': 'ANY'}, ...]
    # Farmer: state='PA', city='Belém'
    location_match = False
    buyer_targets = buyer.get('targets', [])
    farmer_state = farmer.get('state')
    farmer_city = farmer.get('city')

    for target in buyer_targets:
        if target['state'] == farmer_state:
            if target['city'] == 'ANY' or target['city'] == farmer_city:
                location_match = True
                break

    if not location_match: return False

    # 2. 品种匹配
    if buyer.get('race') != "Any" and buyer.get('race') != farmer.get('race'):
        return False

    # 3. 年龄匹配
    buyer_min = buyer.get('ageMin') or 0
    buyer_max = buyer.get('ageMax') or 100
    if not (buyer_min <= farmer.get('age', 0) <= buyer_max):
        return False

    return True

def scan_for_matches(new_record: Dict, target_db_name: str, is_new_record_farmer: bool):
    targets = db.load(target_db_name)
    matches = []

    for target in targets:
        farmer = new_record if is_new_record_farmer else target
        buyer = target if is_new_record_farmer else new_record

        if check_match(farmer, buyer):
            matches.append(target)

            # --- 1. 通知新提交者 (API发起人) ---
            if 'owner_id' in new_record:
                details = {
                    "role": "Matched with " + ("Buyer" if is_new_record_farmer else "Farmer"),
                    "contact": target.get('contact'),
                    "race": target.get('race'),
                    "qty": target.get('quantity'),
                    "location": target.get('city', 'Unknown')
                }
                # A. 站内信
                save_notification(new_record['owner_id'], "Match Found: New Deal Available!", details)
                # B. 发送邮件 (如果 contact 字段看起来像邮箱)
                send_match_email(
                    to_email=new_record.get('contact', ''),
                    subject="Match Found: New Deal Available!",
                    match_details=details
                )

            # --- 2. 通知旧数据拥有者 (被动匹配) ---
            if 'owner_id' in target:
                details = {
                    "role": "New " + ("Farmer" if not is_new_record_farmer else "Buyer") + " matched you",
                    "contact": new_record.get('contact'),
                    "race": new_record.get('race'),
                    "qty": new_record.get('quantity'),
                    "location": new_record.get('city', 'Unknown')
                }
                # A. 站内信
                save_notification(target['owner_id'], "New Interest in your Listing!", details)
                # B. 发送邮件
                send_match_email(
                    to_email=target.get('contact', ''),
                    subject="New Interest in your Listing!",
                    match_details=details
                )

    return len(matches)