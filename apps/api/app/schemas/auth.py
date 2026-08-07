from pydantic import BaseModel


class AuthUser(BaseModel):
    id: str
    display_name: str
    instagram_username: str
    email: str

