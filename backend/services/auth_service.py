from sqlalchemy.orm import Session
from sqlalchemy import select

from pwdlib import PasswordHash

from backend.models import User
from backend.schemas.auth import RegisterRequest
from sqlalchemy.exc import IntegrityError
from backend.schemas.auth import RegisterRequest, LoginRequest


password_hash = PasswordHash.recommended()

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)
def login_user(db: Session, data: LoginRequest):
    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if not user:
        raise ValueError("Invalid username or password")

    if not verify_password(data.password, user.password_hash):
        raise ValueError("Invalid username or password")

    return user


def register_user(db: Session, data: RegisterRequest):
    # 1. Kiểm tra username đã tồn tại
    existing_username = db.scalar(
        select(User).where(User.username == data.username)
    )

    if existing_username:
        raise ValueError("Username already exists")

    # 2. Kiểm tra email đã tồn tại
    existing_email = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_email:
        raise ValueError("Email already exists")

    # 3. Hash password
    hashed_password = password_hash.hash(data.password)

    # 4. Tạo User mới
    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed_password
    )

    # 5. Lưu vào database
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Username or email already exists")

    db.refresh(new_user)

    return new_user