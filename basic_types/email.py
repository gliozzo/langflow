from pydantic import BaseModel

class Email(BaseModel):
    to: str | None = None
    email: str | None = None
    subject: str | None = None
    body: str | None = None




