from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class ContactSchema(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True)
    name:str = Field(..., min_length=2)
    email:EmailStr
    phone: str = Field(
    ...,
    pattern=r"^\+?[0-9]{10,15}$"
)
    subject: Optional[str] = None
    message: str= Field(..., min_length=1)