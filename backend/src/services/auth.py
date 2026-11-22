from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.settings import CACHE, JWT_SECRET
from src.models.db import one, transaction
from src.utils.crypto import check_password

bearer = HTTPBearer(auto_error=False)


def login(payload, address):
    key = f'flow:login:{address}'
    with CACHE.pipeline(transaction=True) as pipe:
        attempts, _ = pipe.incr(key).expire(key, 60, nx=True).execute()
    if attempts > 60:
        raise HTTPException(429, '登录请求过多，请稍后重试')
    with transaction() as cursor:
        user = one(cursor, 'SELECT * FROM users WHERE username=%s', (payload.username,))
    if not user or not check_password(payload.password, user['password_hash']):
        raise HTTPException(401, '账号或口令有误')
    user.pop('password_hash')
    token = jwt.encode({'sub': user['username'], 'exp': datetime.now(timezone.utc) + timedelta(hours=8)},
                       JWT_SECRET, algorithm='HS256')
    return {'token': token, 'user': user}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        username = jwt.decode(credentials.credentials if credentials else '', JWT_SECRET,
                              algorithms=['HS256'], options={'require': ['exp', 'sub']})['sub']
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, '请登录后继续') from exc
    with transaction() as cursor:
        user = one(cursor, 'SELECT username,display_name,role FROM users WHERE username=%s', (username,))
    if not user:
        raise HTTPException(401, '账号已失效')
    return user


def roles(*allowed):
    def check(user=Depends(current_user)):
        if user['role'] not in allowed:
            raise HTTPException(403, '当前席位无权执行此操作')
        return user
    return check
