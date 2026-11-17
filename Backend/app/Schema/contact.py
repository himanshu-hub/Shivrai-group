from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ContactSchema(BaseModel):

    name:str = Field(..., min_length=2)
    email:EmailStr
    phone:str = Field(..., min_length=10, max_length=15)
    subject: Optional[str] = None
    message: str= Field(..., min_length=1)