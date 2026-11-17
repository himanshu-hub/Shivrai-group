from pydantic import BaseModel, EmailStr
from typing import Optional


class ContactSchema(BaseModel):

    name:str
    email:EmailStr
    phone:str
    subject: Optional[str] = None
    message: str