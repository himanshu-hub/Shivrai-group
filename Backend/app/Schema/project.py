
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


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
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    name: str = Field(..., min_length=2)
    status: ProjectStatus
    category: ProjectCategory
    location: str = Field(..., min_length=2)
    description: str = Field(..., min_length=1)


class ProjectUpdateSchema(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    name: str | None = Field(
        default=None,
        min_length=2
    )
    status: ProjectStatus | None = None
    category: ProjectCategory | None = None
    location: str | None = Field(
        default=None,
        min_length=2
    )
    description: str | None = Field(
        default=None,
        min_length=1
    )


class GalleryAssetResponse(BaseModel):
    url: str
    public_id: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    status: ProjectStatus
    category: ProjectCategory
    location: str
    description: str

    image: str | None = None
    image_public_id: str | None = None
    gallery: list[str] = Field(default_factory=list)
    gallery_assets: list[GalleryAssetResponse] = Field(
        default_factory=list
    )

    total_views: int = 0
    daily_views: dict[str, int] = Field(
        default_factory=dict
    )
    created_at: datetime | None = None


class ProjectListResponse(BaseModel):
    total_projects: int
    current_page: int
    total_pages: int
    projects: list[ProjectResponse] = Field(
        default_factory=list
    )
