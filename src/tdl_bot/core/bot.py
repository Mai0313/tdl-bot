"""Telegram Bot module for handling forwarded messages and downloading media."""

import re
import asyncio
import logging

from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

from tdl_bot.utils.config import Config
from tdl_bot.core.downloader import download_from_urls

logger = logging.getLogger(__name__)

# Pattern to match Telegram message links
_TG_URL_PATTERN = re.compile(r"https?://t\.me/\S+")

# Buffer to collect media group messages: media_group_id -> list of urls
_media_group_buffers: dict[str, list[str]] = {}
# Keep track of scheduled tasks so we only process each group once
_media_group_tasks: dict[str, asyncio.Task] = {}
# Store the first message of each group so we can reply to it
_media_group_messages: dict[str, Update] = {}

# How long to wait (seconds) for more messages in the same media group
_MEDIA_GROUP_WAIT = 1.5


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


def _extract_urls_from_message(message: Message) -> list[str]:
    """Extract all Telegram URLs from a message (text, caption, forward origin).

    Args:
        message: The Telegram message object.

    Returns:
        A list of unique Telegram URLs found in / derived from the message.
    """
    urls: list[str] = []

    # 1. Extract URLs from text / caption
    text = message.text or message.caption or ""
    urls.extend(_extract_telegram_urls(text))

    # 2. If this is a forwarded message, try to build a link from the origin
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

    return urls


async def _process_media_group(
    media_group_id: str, chat_id: int, context: CallbackContext
) -> None:
    """Wait for all messages in a media group, then download them.

    Args:
        media_group_id: The media group id to process.
        chat_id: The chat id to reply in.
        context: The callback context.
    """
    # Wait a bit to let all messages in the group arrive
    await asyncio.sleep(_MEDIA_GROUP_WAIT)

    urls = _media_group_buffers.pop(media_group_id, [])
    update = _media_group_messages.pop(media_group_id, None)
    _media_group_tasks.pop(media_group_id, None)

    if not urls or update is None:
        return

    message = update.message

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    status_msg = await message.reply_text(
        f"⏬ Downloading from {len(unique_urls)} link(s)...\nPlease wait."
    )

    download_dir, success, result_msg = await download_from_urls(unique_urls)

    if success:
        downloaded_files = [f for f in download_dir.iterdir() if f.is_file()]
        file_list = "\n".join(f"  📄 <code>{f.name}</code>" for f in downloaded_files)
        reply = (
            f"✅ Download completed!\n\n"
            f"📁 Saved to: <code>{download_dir}</code>\n"
            f"📦 Files ({len(downloaded_files)}):\n{file_list}"
        )
    else:
        reply = f"❌ Download failed.\n\n{result_msg}"

    await status_msg.edit_text(reply, parse_mode="HTML")


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

    For media group messages (multiple photos/videos forwarded together),
    a buffer collects all links and processes them as a batch after a short
    delay.

    Args:
        update: The incoming update.
        context: The callback context.
    """
    message = update.message
    if message is None:
        return

    urls = _extract_urls_from_message(message)

    # --- Media Group handling ---
    if message.media_group_id is not None:
        group_id = message.media_group_id

        if group_id not in _media_group_buffers:
            _media_group_buffers[group_id] = []
            _media_group_messages[group_id] = update

        _media_group_buffers[group_id].extend(urls)

        # Cancel the previous timer and reset it so we always wait from the
        # latest message in the group.
        existing_task = _media_group_tasks.get(group_id)
        if existing_task is not None:
            existing_task.cancel()

        _media_group_tasks[group_id] = asyncio.create_task(
            _process_media_group(group_id, message.chat_id, context)
        )
        return

    # --- Single message handling ---
    if not urls:
        await message.reply_text(
            "⚠️ I couldn't find any Telegram links in this message.\n"
            "Please forward a message from a channel/group or send me a https://t.me/... link."
        )
        return

    status_msg = await message.reply_text(
        f"⏬ Downloading from {len(urls)} link(s)...\nPlease wait."
    )

    download_dir, success, result_msg = await download_from_urls(urls)

    if success:
        downloaded_files = [f for f in download_dir.iterdir() if f.is_file()]
        file_list = "\n".join(f"  📄 <code>{f.name}</code>" for f in downloaded_files)
        reply = (
            f"✅ Download completed!\n\n"
            f"📁 Saved to: <code>{download_dir}</code>\n"
            f"📦 Files ({len(downloaded_files)}):\n{file_list}"
        )
    else:
        reply = f"❌ Download failed.\n\n{result_msg}"

    await status_msg.edit_text(reply, parse_mode="HTML")


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
