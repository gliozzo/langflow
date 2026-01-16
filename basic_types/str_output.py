from pydantic import BaseModel
from typing import Optional
class StringOutput(BaseModel):
    value:Optional[str]=None