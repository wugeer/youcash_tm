from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.db import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserOut, Token, UserLogin

router = APIRouter()

# OAuth2密码模式，用于令牌获取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """根据JWT令牌获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有足够的权限")
    return current_user

@router.post("/register", response_model=UserOut)
def register(*, db: Session = Depends(get_db), user_in: UserCreate):
    """注册新用户"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    db_user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        is_active=True,
        is_admin=False  # 默认不是管理员
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """用户登录获取令牌"""
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
def login_json(db: Session = Depends(get_db), user_login: UserLogin = Body(...)):
    """通过JSON方式登录（便于前端使用）"""
    # 查找用户
    user = db.query(User).filter(User.username == user_login.username).first()
    if not user or not verify_password(user_login.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/create-admin", response_model=UserOut)
def create_admin_user(
    *, 
    db: Session = Depends(get_db), 
    user_create: UserCreate
):
    """创建管理员用户（第一次使用系统时）"""
    # 检查是否已存在用户
    user_count = db.query(User).count()
    if user_count > 0:
        # 如果系统中已有用户，只有管理员才能创建其他管理员
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已初始化，只有管理员可以创建其他管理员"
        )
    
    # 如果系统中没有用户，允许创建第一个管理员账户
    db_user = db.query(User).filter(User.username == user_create.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    db_user = User(
        username=user_create.username,
        password_hash=get_password_hash(user_create.password),
        is_active=True,
        is_admin=True  # 设置为管理员
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
