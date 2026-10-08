import sys
import os

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

db = SessionLocal()
users = db.query(User).all()
print("Registered users count:", len(users))
for u in users:
    print(f"User ID: {u.id}, Email: {u.email}, Role: {getattr(u, 'role', 'N/A')}")

candidate = db.query(User).filter(User.email == "candidate@vidyamarg.ai").first()
if candidate:
    candidate.password_hash = get_password_hash("password")
    db.commit()
    print("SUCCESS: Reset password for candidate@vidyamarg.ai to 'password'")
else:
    new_cand = User(
        email="candidate@vidyamarg.ai",
        full_name="Candidate User",
        password_hash=get_password_hash("password"),
        role="candidate"
    )
    db.add(new_cand)
    db.commit()
    print("SUCCESS: Created candidate@vidyamarg.ai with password 'password'")
