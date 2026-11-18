from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import(
    create_access_token,
    verify_password,
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def admin_logic(
    credentials: OAuth2PasswordRequestForm = Depends()
):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=500,
            detail="Admin authentication is not configured"
        )

    if credentials.username != ADMIN_USERNAME or not verify_password(
        credentials.password,
        ADMIN_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(
        {"sub": credentials.username}
    )

    return {
        "access_token": access_token,
        "token_type":"bearer"
    }