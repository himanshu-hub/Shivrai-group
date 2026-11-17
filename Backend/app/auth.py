import os
import jwt
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

load_dotenv()

password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")


#lYYdgzosenS9Nao9qqNSVz6_MjWfoAWtIo3be5-UsqrymadoI47Up1A7BW4Tv78sckKs51hu3ecOF_4YXkQJrQ
#$env:JWT_SECRET_KEY="lYYdgzosenS9Nao9qqNSVz6_MjWfoAWtIo3be5-UsqrymadoI47Up1A7BW4Tv78sckKs51hu3ecOF_4YXkQJrQ"
#$env:ADMIN_USERNAME="admin"
#$argon2id$v=19$m=65536,t=3,p=4$CJiE/5Z93ew9pIwsHzvHtg$Myh8fJJoP/O9foUasqD9Js7MIeJwEu9q9gwKIfuyiNM
#$env:ADMIN_PASSWORD_HASH="$argon2id$v=19$m=65536,t=3,p=4$CJiE/5Z93ew9pIwsHzvHtg$Myh8fJJoP/O9foUasqD9Js7MIeJwEu9q9gwKIfuyiNM"


#m=65536,t=3,p=4$EJZgE2/7i0ywGZWutecBvA$VVebJw686yAgjYm9aBj9AhRMbrHjIpRDi19ywPX+6gw
#$env:ADMIN_PASSWORD_HASH='$argon2id$v=19$m=65536,t=3,p=4$EJZgE2/7i0ywGZWutecBvA$VVebJw686yAgjYm9aBj9AhRMbrHjIpRDi19ywPX+6gw'




ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes= ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm= ALGORITHM
    )

def get_password_hash(password: str):
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)

def verify_access_token(token: str):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    
    except jwt.InvalidTokenError:
        return None    
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate":"Bearer"}
        )

    username = payload.get("sub")

    if username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authentication":"Bearer"}
        )

    return username 