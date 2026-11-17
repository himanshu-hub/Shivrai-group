from pydantic import BaseModel
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from pydantic import ConfigDict

class ProjectStatus(str, Enum):
    ongoing = "Ongoing"
    completed = "Completed"
    upcoming = "Upcoming"

class ProjectCategory(str, Enum):
    residential = "Residential"
    commercial = "Commercial"
    retail = "Retail"
    offices = "Offices"

class ProjectSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace= True)
    name: str = Field(..., min_length =2)
    status: ProjectStatus
    category: ProjectCategory
    location: str = Field(..., min_length= 2)
    description: str = Field(..., min_length= 1)
    image: Optional[str] = None