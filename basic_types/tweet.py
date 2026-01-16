from pydantic import BaseModel, Field
from typing import Optional
class Tweet(BaseModel):
    tweet: Optional[str] = Field(None, description="Generate a Tweet to advertise the movie")