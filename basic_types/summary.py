from pydantic import BaseModel
from typing import Optional


class Summary(BaseModel):
    summary: Optional[str] = None
   