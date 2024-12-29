import re
from pathlib import Path

# import anyio
# import httpx
import logfire
from pydantic import Field, AliasChoices
from telegram import Bot, Update, PhotoSize
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from pydantic_settings import BaseSettings

from tdl.processor import TDLManager

logfire.configure(send_to_logfire=False)


class Config(BaseSettings):
    telegram_token: str = Field(
        ..., validation_alias=AliasChoices("TELEGRAM_TOKEN", "TOKEN", "token")
    )


config = Config()


async def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message.photo or update.message.video:
        # 下載時需要
        post_id: int = update.message.api_kwargs["forward_from_message_id"]
        # >>> Output: 156

        message_id: int = update.message.api_kwargs["forward_from_chat"]["id"]
        # >>> Output: -1001128501931

        # 發送這訊息的使用者名稱
        post_sender: str = update.message.api_kwargs["forward_from_chat"]["username"]
        # >>> Output: wanjianxiuxishi

        # 聊天室名稱當資料夾名稱
        post_chatname: str = update.message.api_kwargs["forward_from_chat"]["title"]
        # >>> Output: 晚间休息室🔞
        output_path = Path(f"./downloads/{post_chatname}")

        if update.message.video:
            video_filename_ = update.message.video.file_name
            video_filename = re.sub(r'[\/\\:*?"<>| ]', "_", video_filename_)

            output_filename = f"{abs(message_id) % 10000000000}_{post_id}_{video_filename}"
            current_filename = output_path.glob(f"{output_filename}*")
            len(list(current_filename))

        file_url = f"https://t.me/{post_sender}/{post_id}"

        if update.message.photo:
            # 選擇最高解析度的圖片（通常是列表中的最後一個）
            highest_resolution_photo: PhotoSize = max(
                update.message.photo, key=lambda p: p.file_size
            )
            # 獲取圖片文件的完整連結
            bot_: Bot = context.bot
            file_ = await bot_.get_file(highest_resolution_photo.file_id)
            file_url = file_.file_path
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(url=file_url)
            #     response.json()
            #     async with await anyio.open_file(
            #         f"{output_path.as_posix()}/{post_id}.jpg", "wb"
            #     ) as file:
            #         await file.write(response.content)
    else:
        if update.message.text.startswith("https://t.me/"):
            post_id = update.message.text.split("/")[-1]
            post_sender = update.message.text.split("/")[-2]
            file_url = update.message.text
        else:
            logfire.info("Received a text message", text=update.message.text)
            return await update.message.reply_text("好色喔 但你不會用對吧 嘿嘿")
    logfire.info("Message Details", post_id=post_id, post_sender=post_sender, url=file_url)
    td = TDLManager(
        func="download",
        serve=False,
        skip_same=True,
        limit=4,
        pool=0,
        threads=8,
        output_path=output_path,
    )
    td.run(url=file_url)
    return await update.message.reply_text(
        f"下載完成!\nFile URL: {file_url}\nFolder: {output_path.as_posix()}"
    )


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("轉發訊息或提供一個連結，我會幫你下載的!")


def main() -> None:
    bot_token = config.telegram_token
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
