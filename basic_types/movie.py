from pydantic import BaseModel
from typing import Optional
class Movie(BaseModel):
    movie_name: Optional[str] = (
        None  ## Note that fields name should match the column name in the input csv
    )
    genre: Optional[str] = None
    description: Optional[str] = None