from pydantic import BaseModel, Field, ConfigDict

class AdminLoginSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace= True)

    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)