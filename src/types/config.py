from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    token: str = Field(..., validation_alias=AliasChoices("TELEGRAM_TOKEN", "TOKEN", "token"))
