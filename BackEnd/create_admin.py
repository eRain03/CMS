# create_admin.py
import json
import time
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    print("Creating Super Admin...")
    username = input("Enter Admin Username: ")
    password = input("Enter Admin Password: ")

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    # 检查是否存在
    if any(u['username'] == username for u in users):
        print("User already exists!")
        return

    new_admin = {
        "username": username,
        "password": pwd_context.hash(password),
        "email": "admin@platform.com",
        "first_name": "Super",
        "last_name": "Admin",
        "phone": "00000000",
        "address": "HQ",
        "role": "admin", # 关键字段
        "created_at": time.time()
    }

    users.append(new_admin)

    with open("./data/users.json", "w") as f:
        json.dump(users, f, indent=4)

    print(f"✅ Admin {username} created successfully!")

if __name__ == "__main__":
    create_admin()
