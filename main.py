import logfire
from telegram import Update
from rich.console import Console
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from src.types.config import Config
from src.utils.processor import DownloadProcessor

logfire.configure(send_to_logfire=False)
console = Console()
config = Config()


async def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message.photo or update.message.video:
        # 下載時需要
        post_id: int = update.message.api_kwargs["forward_from_message_id"]
        # >>> Output: 156

        # 發送這訊息的使用者名稱
        post_sender: str = update.message.api_kwargs["forward_from_chat"]["username"]
        # >>> Output: wanjianxiuxishi

        # 聊天室名稱當資料夾名稱
        post_chatname: str = update.message.api_kwargs["forward_from_chat"]["title"]
        # >>> Output: 晚间休息室🔞

        file_url = f"https://t.me/{post_sender}/{post_id}"

        if update.message.photo:
            # 選擇最高解析度的圖片（通常是列表中的最後一個）
            highest_resolution_photo = max(update.message.photo, key=lambda p: p.file_size)
            # 獲取圖片文件的完整連結
            _file = await context.bot.get_file(highest_resolution_photo.file_id)
            file_url = _file.file_path
    else:
        if update.message.text.startswith("https://t.me/"):
            post_id = update.message.text.split("/")[-1]
            post_sender = update.message.text.split("/")[-2]
            post_chatname = "private chat"
            file_url = update.message.text
        else:
            logfire.info("Received a text message", text=update.message.text)
            return await update.message.reply_text("好色喔 但你不會用對吧 嘿嘿")
    logfire.info(
        "Message Details",
        post_id=post_id,
        post_sender=post_sender,
        post_chatname=post_chatname,
        url=file_url,
    )
    td = DownloadProcessor(
        func="download", serve=False, skip_same=True, limit=4, pool=0, threads=8
    )
    td.run(url=file_url)
    return await update.message.reply_text(
        f"Post ID: {post_id}\nPost Sender: {post_sender}\nChat Name: {post_chatname}\nFile URL: {file_url}"
    )


# 啟動命令的處理函數
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Hello! Send me a message with a photo or video, and I will print out the highest resolution photo or video link."
    )


# 主函數
def main() -> None:
    bot_token = config.token
    application = Application.builder().token(bot_token).build()

    # 添加處理程序
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(MessageHandler(filters.ATTACHMENT, handle_message))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # 開始執行 bot
    application.run_polling()


if __name__ == "__main__":
    main()
