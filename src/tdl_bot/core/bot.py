"""Telegram Bot module for handling forwarded messages and downloading media."""

import re
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

from tdl_bot.utils.config import Config
from tdl_bot.core.downloader import download_from_urls

logger = logging.getLogger(__name__)

# Pattern to match Telegram message links
_TG_URL_PATTERN = re.compile(r"https?://t\.me/\S+")


def _extract_telegram_urls(text: str) -> list[str]:
    """Extract Telegram URLs from text.

    Args:
        text: The text to extract URLs from.

    Returns:
        A list of Telegram URLs found in the text.
    """
    return _TG_URL_PATTERN.findall(text)


def _build_forward_link(chat_username: str | None, chat_id: int, message_id: int) -> str:
    """Build a Telegram message link from forwarded message metadata.

    If the original chat has a public username, the link is constructed as
    ``https://t.me/{username}/{message_id}``.  Otherwise the numeric chat id
    is used: ``https://t.me/c/{chat_id}/{message_id}`` (private / supergroup
    channels).

    Args:
        chat_username: The public username of the original chat (may be None).
        chat_id: The numeric chat id of the original chat.
        message_id: The message id in the original chat.

    Returns:
        A Telegram message link string.
    """
    if chat_username:
        return f"https://t.me/{chat_username}/{message_id}"
    # Private channels / supergroups: strip the -100 prefix
    raw_id = str(chat_id)
    if raw_id.startswith("-100"):
        raw_id = raw_id[4:]
    return f"https://t.me/c/{raw_id}/{message_id}"


async def _handle_start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command.

    Args:
        update: The incoming update.
        context: The callback context.
    """
    await update.message.reply_text(
        "👋 Hi! Forward me a message from any Telegram channel or group, "
        "and I will download the media (photos & videos) for you.\n\n"
        "You can also send me a Telegram message link directly."
    )


async def _handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages — forwarded or containing Telegram links.

    This handler does the following:
    1. Tries to extract Telegram URLs from the message text / caption.
    2. If the message is forwarded, constructs a link from the forward metadata.
    3. Calls the tdl downloader with the collected URLs.
    4. Replies to the user with the download result.

    Args:
        update: The incoming update.
        context: The callback context.
    """
    message = update.message
    if message is None:
        return

    urls: list[str] = []

    # 1. Extract URLs from text / caption
    text = message.text or message.caption or ""
    urls.extend(_extract_telegram_urls(text))

    # 2. If this is a forwarded message, try to build a link
    if message.forward_origin is not None:
        origin = message.forward_origin
        # MessageOriginChannel has chat & message_id
        if hasattr(origin, "chat") and hasattr(origin, "message_id"):
            chat = origin.chat
            link = _build_forward_link(
                chat_username=chat.username, chat_id=chat.id, message_id=origin.message_id
            )
            if link not in urls:
                urls.append(link)

    if not urls:
        await message.reply_text(
            "⚠️ I couldn't find any Telegram links in this message.\n"
            "Please forward a message from a channel/group or send me a https://t.me/... link."
        )
        return

    # 3. Acknowledge & start download
    status_msg = await message.reply_text(
        f"⏬ Downloading from {len(urls)} link(s)...\nPlease wait."
    )

    download_dir, success, result_msg = await download_from_urls(urls)

    # 4. Reply with result
    if success:
        # Count downloaded files
        downloaded_files = [f for f in download_dir.iterdir() if f.is_file()]
        file_list = "\n".join(f"  📄 `{f.name}`" for f in downloaded_files)
        reply = (
            f"✅ Download completed!\n\n"
            f"📁 Saved to: `{download_dir}`\n"
            f"📦 Files ({len(downloaded_files)}):\n{file_list}"
        )
    else:
        reply = f"❌ Download failed.\n\n{result_msg}"

    await status_msg.edit_text(reply, parse_mode="Markdown")


def create_bot(config: Config) -> Application:
    """Create and configure the Telegram Bot application.

    Args:
        config: The application configuration containing the bot token.

    Returns:
        A configured Telegram Bot Application ready to be started.
    """
    app = Application.builder().token(config.token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", _handle_start))
    app.add_handler(CommandHandler("help", _handle_start))

    # Handle all messages (forwarded or with text/caption containing links)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, _handle_message))

    logger.info("Bot handlers registered successfully.")
    return app
