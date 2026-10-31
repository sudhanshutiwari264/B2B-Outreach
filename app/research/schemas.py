from typing import Optional

from pydantic import BaseModel


class ExtractedContent(BaseModel):
    url: str
    success: bool
    title: Optional[str] = None
    text: Optional[str] = None
    published_at: Optional[str] = None
    content_hash: Optional[str] = None
    extraction_method: str = "none"
    error: Optional[str] = None
    restricted: bool = False
