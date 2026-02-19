from typing import Any
from pathlib import Path

import logfire
from pydantic import Field, BaseModel, ConfigDict, model_validator
from telethon import TelegramClient
from telethon.tl.types import User
from telethon.tl.patched import Message
from telethon.tl.custom.dialog import Dialog

from utils.config import Config

logfire.configure(send_to_logfire=False)


class TelegramDialog(BaseModel):
    channel_name: str
    channel_id: int


class TelegramMessage(BaseModel):
    url: str
    text: str | None | Any


class TelegramManager(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: TelegramClient = Field(
        default=None,
        title="Telegram Client",
        description="Telethon client for interacting with Telegram API, it will be initialized after the model is created.",
    )

    @model_validator(mode="after")
    def _setup_client(self) -> "TelegramManager":
        config = Config()
        session_path = Path("./data/my_session.session")
        session_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = TelegramClient(
            session=session_path, api_id=config.api_id, api_hash=config.api_hash
        )
        return self

    async def get_personal_info(self) -> User:
        me = await self.client.get_me()
        if not isinstance(me, User):
            raise ValueError("You are not logged in.")
        return me

    async def get_channel_names(self) -> list[TelegramDialog]:
        result = []
        async for dialog in self.client.iter_dialogs():
            if isinstance(dialog, Dialog):
                telegram_dialog = TelegramDialog(channel_name=dialog.name, channel_id=dialog.id)
                result.append(telegram_dialog)
        return result

    async def get_channel_messages(self, channel_name: str) -> list[TelegramMessage]:
        channel = await self.client.get_entity(channel_name)
        result = []
        async for message in self.client.iter_messages(channel):
            if isinstance(message, Message) and (message.photo or message.video):
                url = f"https://t.me/c/{channel.id}/{message.id}"
                logfire.info("Found media message", url=url)
                result.append(TelegramMessage(url=url, text=message.text))
        return result

    async def get_all_messages(self) -> None:
        await self.client.start()
        me = await self.get_personal_info()
        logfire.info("Logged in as", phone=me.phone)

        channels = await self.get_channel_names()
        for channel in channels:
            messages = await self.get_channel_messages(channel_name=channel.channel_name)
            for message in messages:
                logfire.info("Fetched messages", **message.model_dump())
                break
            break


if __name__ == "__main__":
    telegram = TelegramManager()
    with telegram.client:
        telegram.client.loop.run_until_complete(telegram.get_all_messages())
