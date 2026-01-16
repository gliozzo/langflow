from pydantic import BaseModel
from typing import Optional
class Answer(BaseModel):
    short_answer:Optional[str]=None
    long_answer:Optional[str]=None