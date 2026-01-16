from pydantic import BaseModel
from typing import Optional, Any
class GenericInput(BaseModel):
    value:Optional[Any]=None