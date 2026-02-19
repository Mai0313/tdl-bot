import dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

dotenv.load_dotenv()


class Config(BaseSettings):
    token: str = Field(
        ...,
        validation_alias="TELEGRAM_TOKEN",
        description="Telegram Bot Token, get this from https://telegram.me/BotFather",
    )
    api_id: int = Field(
        ...,
        validation_alias="TELEGRAM_API_ID",
        description="API ID for Telegram, get this from https://my.telegram.org/auth",
    )
    api_hash: str = Field(
        ...,
        validation_alias="TELEGRAM_API_HASH",
        description="API Hash for Telegram, get this from https://my.telegram.org/auth",
    )
