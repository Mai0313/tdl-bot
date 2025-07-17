import re
import asyncio
from pathlib import Path
from datetime import datetime
from collections import deque, defaultdict
from dataclasses import field, dataclass

import logfire
from pydantic import Field, BaseModel
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

from src.utils.config import Config
from src.core.processor import TelegramDownloader

logfire.configure(send_to_logfire=False)


class MessageInfo(BaseModel):
    """Information extracted from a Telegram message.

    Attributes:
        post_id (str): The ID of the post
        post_sender (str): The sender username
        post_chatname (str): The chat name for folder creation
        file_url (str): The URL to download from
    """

    post_id: str = Field(..., description="The ID of the post")
    post_sender: str = Field(..., description="The sender username")
    post_chatname: str = Field(..., description="The chat name for folder creation")
    file_url: str = Field(..., description="The URL to download from")


@dataclass
class DownloadTask:
    """A download task containing message info and Telegram context."""

    message_info: MessageInfo
    update: Update
    processing_msg_id: int | None = None
    added_at: datetime = field(default_factory=datetime.now)


class BatchDownloadManager:
    """Manages batch downloads for improved efficiency."""

    def __init__(self):
        """Initialize batch download manager with fixed settings."""
        self.batch_size = 20  # Fixed batch size
        self.batch_timeout = 3.0  # Fixed timeout in seconds
        self.download_queue: deque[DownloadTask] = deque()
        self.processing = False
        self._batch_task: asyncio.Task | None = None
        self._new_task_event = asyncio.Event()

    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown special characters in text.

        Args:
            text (str): Text to escape

        Returns:
            str: Escaped text safe for Markdown
        """
        # Escape Telegram Markdown special characters
        special_chars = [
            "_",
            "*",
            "[",
            "]",
            "(",
            ")",
            "~",
            "`",
            ">",
            "#",
            "+",
            "-",
            "=",
            "|",
            "{",
            "}",
            ".",
            "!",
        ]
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f"\\{char}")
        return escaped_text

    async def add_download_task(self, task: DownloadTask) -> None:
        """Add a download task to the batch queue.

        Args:
            task (DownloadTask): The download task to add
        """
        self.download_queue.append(task)
        self._new_task_event.set()  # Signal that a new task was added
        logfire.info(
            "Added download task to queue",
            url=task.message_info.file_url,
            queue_size=len(self.download_queue),
        )

        # Check if this is the first task with this message ID
        same_message_tasks = [
            t for t in self.download_queue if t.processing_msg_id == task.processing_msg_id
        ]

        # Only update the message for the first task with this message ID
        if len(same_message_tasks) == 1:
            await self._update_task_message(
                task,
                f"⏳ 已加入下載隊列... (隊列中: {len(self.download_queue)} 個任務)",
                use_markdown=False,
            )

        # Start batch processing if not already running
        if not self.processing:
            await self._start_batch_processing()

    async def _start_batch_processing(self) -> None:
        """Start the batch processing task."""
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._process_batches())

    async def _process_batches(self) -> None:
        """Process download tasks in batches."""
        self.processing = True

        try:
            while self.download_queue:
                batch_start_time = datetime.now()
                current_batch: list[DownloadTask] = []

                # Collect tasks for batch processing
                while (
                    len(current_batch) < self.batch_size
                    and self.download_queue
                    and (datetime.now() - batch_start_time).total_seconds() < self.batch_timeout
                ):
                    # Check if we should wait for more tasks or process now
                    if not current_batch:
                        # Always take at least one task
                        current_batch.append(self.download_queue.popleft())
                    elif len(self.download_queue) == 0:
                        # No more tasks, wait for new ones using Event
                        try:
                            await asyncio.wait_for(self._wait_for_new_tasks(), timeout=1.0)
                        except asyncio.TimeoutError:
                            break
                    else:
                        # Add more tasks to current batch
                        current_batch.append(self.download_queue.popleft())

                if current_batch:
                    await self._process_batch(current_batch)

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)

        finally:
            self.processing = False

    async def _wait_for_new_tasks(self) -> None:
        """Wait for new tasks to be added to the queue using asyncio.Event."""
        self._new_task_event.clear()
        await self._new_task_event.wait()

    async def _process_batch(self, batch: list[DownloadTask]) -> None:
        """Process a batch of download tasks.

        Args:
            batch (List[DownloadTask]): List of download tasks to process
        """
        # Group tasks by output directory for efficient downloading
        grouped_tasks: dict[str, list[DownloadTask]] = defaultdict(list)

        for task in batch:
            output_dir = f"./data/{task.message_info.post_chatname}"
            grouped_tasks[output_dir].append(task)

        logfire.info("Processing batch", batch_size=len(batch), groups=len(grouped_tasks))

        # Process each group and track the last processed task for final update
        total_groups = len(grouped_tasks)
        last_processed_task = None

        for i, (output_dir, tasks) in enumerate(grouped_tasks.items(), 1):
            remaining_groups = total_groups - i
            await self._download_group(output_dir, tasks, remaining_groups)
            last_processed_task = tasks[0]  # Remember the primary task

        # After all groups are processed, update the final message to show completion
        if last_processed_task and total_groups > 1:
            await self._update_final_completion_message(last_processed_task)

    async def _update_final_completion_message(self, task: DownloadTask) -> None:
        """Update the final message to show all downloads are completed.

        Args:
            task (DownloadTask): The task to update
        """
        try:
            if task.processing_msg_id and task.update.message:
                # Get the current message text and update the status part
                final_msg = "🎉 *全部批次處理完成\\!*\n\n✅ 所有下載任務已完成"

                await task.update.get_bot().edit_message_text(
                    chat_id=task.update.effective_chat.id,
                    message_id=task.processing_msg_id,
                    text=final_msg,
                    parse_mode="MarkdownV2",
                )
        except Exception as e:
            logfire.error("Failed to update final completion message", error=str(e))

    async def _download_group(
        self, output_dir: str, tasks: list[DownloadTask], remaining_groups: int = 0
    ) -> None:
        """Download a group of tasks to the same output directory.

        Args:
            output_dir (str): The output directory path
            tasks (List[DownloadTask]): Tasks to download
            remaining_groups (int): Number of remaining groups to process
        """
        urls = [task.message_info.file_url for task in tasks]

        try:
            primary_task = tasks[-1]  # Use the last (most recent) task

            # Update non-primary tasks to show merged status
            await self._update_merged_tasks(tasks[:-1])

            # Update primary message with batch info
            await self._update_primary_task_progress(primary_task, urls, remaining_groups)

            # Perform the actual download
            await self._execute_download(output_dir, urls)

            # Update completion messages
            await self._update_completion_messages(tasks, urls, output_dir, remaining_groups)

        except Exception as e:
            await self._handle_download_error(tasks, urls, e)

    async def _update_merged_tasks(self, tasks: list[DownloadTask]) -> None:
        """Update non-primary tasks to show they're merged.

        Args:
            tasks (List[DownloadTask]): Tasks to update as merged
        """
        for task in tasks:
            if task.processing_msg_id and task.update.message:
                try:
                    await task.update.get_bot().edit_message_text(
                        chat_id=task.update.effective_chat.id,
                        message_id=task.processing_msg_id,
                        text="🔄 已合併到批量下載中...",
                    )
                except Exception as e:
                    logfire.warning("Failed to update merged message", error=str(e))

    async def _update_primary_task_progress(
        self, primary_task: DownloadTask, urls: list[str], remaining_groups: int
    ) -> None:
        """Update the primary task message with progress info.

        Args:
            primary_task (DownloadTask): The primary task to update
            urls (List[str]): List of URLs being downloaded
            remaining_groups (int): Number of remaining groups
        """
        if primary_task.processing_msg_id and primary_task.update.message:
            try:
                if len(urls) == 1:
                    progress_text = "⏳ 開始下載... (1 個檔案)"
                else:
                    progress_text = f"⏳ 批量下載中... ({len(urls)} 個檔案)"

                if remaining_groups > 0:
                    progress_text += f"\n📋 剩餘批次: {remaining_groups} 組"

                await primary_task.update.get_bot().edit_message_text(
                    chat_id=primary_task.update.effective_chat.id,
                    message_id=primary_task.processing_msg_id,
                    text=progress_text,
                )
            except Exception as e:
                logfire.warning("Failed to update processing message", error=str(e))

    async def _execute_download(self, output_dir: str, urls: list[str]) -> None:
        """Execute the actual download operation.

        Args:
            output_dir (str): Directory to download files to
            urls (List[str]): URLs to download
        """
        output_folder = Path(output_dir)
        logfire.info("Starting batch download", urls=urls, output_folder=output_folder.as_posix())

        td = TelegramDownloader(output_folder=output_folder)
        td.download(urls=urls)

    async def _update_completion_messages(
        self, tasks: list[DownloadTask], urls: list[str], output_dir: str, remaining_groups: int
    ) -> None:
        """Update completion messages for all tasks.

        Args:
            tasks (List[DownloadTask]): All tasks in the group
            urls (List[str]): URLs that were downloaded
            output_dir (str): Directory where files were downloaded
            remaining_groups (int): Number of remaining groups
        """
        primary_task = tasks[-1]
        output_folder = Path(output_dir)

        # Create formatted success message
        success_msg = self._create_success_message(urls, output_folder, remaining_groups)

        # Update primary task message
        await self._update_task_message(primary_task, success_msg)

        # Update other merged messages to show completion
        for task in tasks[:-1]:
            if task.processing_msg_id and task.update.message:
                try:
                    merged_msg = f"✅ 已合併完成\n🔗 來源: {self._escape_markdown(task.message_info.file_url)}"
                    await self._update_task_message(task, merged_msg)
                except Exception as e:
                    logfire.warning("Failed to update merged completion message", error=str(e))

        logfire.info("Batch download completed successfully", batch_size=len(urls))

    def _create_success_message(
        self, urls: list[str], output_folder: Path, remaining_groups: int
    ) -> str:
        """Create a formatted success message.

        Args:
            urls (List[str]): URLs that were downloaded
            output_folder (Path): Path where files were downloaded
            remaining_groups (int): Number of remaining groups

        Returns:
            str: Formatted success message
        """
        if len(urls) == 1:
            escaped_path = self._escape_markdown(output_folder.as_posix())
            escaped_url = self._escape_markdown(urls[0])
            success_msg = (
                f"✅ *下載完成\\!*\n\n📁 *資料夾*: `{escaped_path}`\n\n🔗 *來源*: {escaped_url}"
            )
        else:
            escaped_path = self._escape_markdown(output_folder.as_posix())
            url_list = "\n".join([f"• {self._escape_markdown(url)}" for url in urls])
            success_msg = (
                f"✅ *批量下載完成\\!*\n\n"
                f"📁 *資料夾*: `{escaped_path}`\n\n"
                f"🔗 *來源* \\({len(urls)} 個檔案\\):\n{url_list}"
            )

        if remaining_groups > 0:
            success_msg += f"\n\n📋 *剩餘批次*: {remaining_groups} 組待處理"
        else:
            success_msg += "\n\n🎉 *狀態*: 全部下載完成"

        return success_msg

    async def _handle_download_error(
        self, tasks: list[DownloadTask], urls: list[str], error: Exception
    ) -> None:
        """Handle download errors by updating task messages.

        Args:
            tasks (List[DownloadTask]): Tasks that failed
            urls (List[str]): URLs that failed to download
            error (Exception): The error that occurred
        """
        error_msg = f"❌ 批量下載失敗: {error!s}"
        logfire.error("Batch download failed", error=str(error), urls=urls, _exc_info=True)

        # Update primary task message with error (without markdown)
        await self._update_task_message(tasks[-1], error_msg, use_markdown=False)

        # Update other merged messages with error
        for task in tasks[:-1]:
            if task.processing_msg_id and task.update.message:
                try:
                    await self._update_task_message(task, "❌ 批量下載失敗", use_markdown=False)
                except Exception as e:
                    logfire.warning("Failed to update merged error message", error=str(e))

    async def _update_task_message(
        self, task: DownloadTask, message: str, use_markdown: bool = True
    ) -> None:
        """Update a task's message.

        Args:
            task (DownloadTask): The task to update
            message (str): The message to send
            use_markdown (bool): Whether to use Markdown formatting
        """
        try:
            parse_mode = "MarkdownV2" if use_markdown else None
            if task.processing_msg_id and task.update.message:
                await task.update.get_bot().edit_message_text(
                    chat_id=task.update.effective_chat.id,
                    message_id=task.processing_msg_id,
                    text=message,
                    parse_mode=parse_mode,
                )
            elif task.update.message:
                await task.update.message.reply_text(message, parse_mode=parse_mode)
        except Exception as e:
            logfire.error("Failed to update task message", error=str(e))
            # Fallback: try without markdown
            if use_markdown:
                try:
                    await self._update_task_message(task, message, use_markdown=False)
                except Exception as fallback_error:
                    logfire.error("Fallback message update also failed", error=str(fallback_error))


class TelegramBot:
    """Enhanced Telegram Bot for downloading media from Telegram messages."""

    def __init__(self) -> None:
        # More flexible URL pattern to handle various Telegram URL formats
        self.url_pattern = re.compile(r"https://t\.me/([^/\s]+)/(\d+)(?:\S*)?")
        self.batch_manager = BatchDownloadManager()

    def extract_url_info(self, url: str) -> MessageInfo | None:
        """Extract information from a Telegram URL.

        Args:
            url (str): The Telegram URL

        Returns:
            Optional[MessageInfo]: Extracted message information or None if invalid
        """
        # Clean the URL (remove trailing characters that might be included)
        url = url.strip().rstrip(".,;!?")

        match = self.url_pattern.match(url)
        if not match:
            return None

        post_sender, post_id = match.groups()
        post_chatname = f"{post_sender}_{post_id}"

        return MessageInfo(
            post_id=post_id, post_sender=post_sender, post_chatname=post_chatname, file_url=url
        )

    def extract_forwarded_info(self, message: Message) -> MessageInfo | None:
        """Extract information from a forwarded message.

        Args:
            message (Message): The Telegram message object

        Returns:
            Optional[MessageInfo]: Extracted message information or None if invalid
        """
        try:
            if not message.api_kwargs:
                return None

            forward_info = message.api_kwargs.get("forward_from_message_id")
            forward_chat = message.api_kwargs.get("forward_from_chat")

            if not forward_info or not forward_chat:
                return None

            post_id = str(forward_info)
            post_sender = forward_chat.get("username", "unknown")
            post_chatname = forward_chat.get("title", f"{post_sender}_{post_id}")
            file_url = f"https://t.me/{post_sender}/{post_id}"

            return MessageInfo(
                post_id=post_id,
                post_sender=post_sender,
                post_chatname=post_chatname,
                file_url=file_url,
            )
        except (KeyError, TypeError) as e:
            logfire.error("Error extracting forwarded message info", error=str(e))
            return None

    async def download_media_batch(
        self, message_info: MessageInfo, update: Update, reply_msg_id: int
    ) -> None:
        """Add media download to batch queue for efficient processing.

        Args:
            message_info (MessageInfo): The message information
            update (Update): The Telegram update object
            reply_msg_id (int): The ID of the reply message to edit
        """
        # Create download task with existing message ID
        task = DownloadTask(
            message_info=message_info, update=update, processing_msg_id=reply_msg_id
        )

        # Add to batch queue
        await self.batch_manager.add_download_task(task)

    async def download_media(self, message_info: MessageInfo) -> tuple[bool, str]:
        """Download media using TDL Manager (legacy single download method).

        Args:
            message_info (MessageInfo): The message information

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            output_folder = Path(f"./data/{message_info.post_chatname}")
            logfire.info(
                "Starting download",
                post_id=message_info.post_id,
                post_sender=message_info.post_sender,
                url=message_info.file_url,
                output_folder=output_folder.as_posix(),
            )

            td = TelegramDownloader(output_folder=output_folder)
            td.download(urls=[message_info.file_url])

            success_msg = (
                f"✅ 下載完成!\n"
                f"📁 資料夾: {output_folder.as_posix()}\n"
                f"🔗 來源: {message_info.file_url}"
            )
            logfire.info("Download completed successfully")
            return True, success_msg

        except Exception as e:
            error_msg = f"❌ 下載失敗: {e!s}"
            logfire.error("Download failed", error=str(e), _exc_info=True)
            return False, error_msg


# Global bot instance
bot_instance = TelegramBot()


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and process downloads.

    Args:
        update (Update): The Telegram update object
        context (CallbackContext): The callback context
    """
    if not update.message:
        logfire.warning("Received update without message")
        return

    message = update.message
    message_infos = await _extract_message_infos(message)

    # Process message infos if we have any
    if message_infos:
        await _process_download_requests(message_infos, update, message)
    else:
        await message.reply_text("❌ 無法解析訊息內容，請確認格式是否正確")


async def _extract_message_infos(message: Message) -> list[MessageInfo]:
    """Extract message information from a Telegram message.

    Args:
        message (Message): The Telegram message

    Returns:
        List[MessageInfo]: List of extracted message information
    """
    message_infos: list[MessageInfo] = []

    # Handle direct URL messages (check for multiple URLs in text)
    if message.text:
        # Extract all Telegram URLs from the text
        url_pattern = re.compile(r"https://t\.me/[^\s]+")
        found_urls = url_pattern.findall(message.text)

        if found_urls:
            logfire.info("Processing URL message(s)", urls=found_urls)
            for url in found_urls:
                message_info = bot_instance.extract_url_info(url)
                if message_info:
                    message_infos.append(message_info)

    # Handle forwarded media messages
    elif message.photo or message.video:
        logfire.info("Processing forwarded media message")
        message_info = bot_instance.extract_forwarded_info(message)
        if message_info:
            message_infos.append(message_info)

    # Handle other text messages
    else:
        await _handle_unsupported_message(message)

    return message_infos


async def _handle_unsupported_message(message: Message) -> None:
    """Handle unsupported message types.

    Args:
        message (Message): The unsupported message
    """
    text = message.text or "非文字訊息"
    logfire.info("Received unsupported message", text=text)
    await message.reply_text(
        "🤖 請發送以下格式的訊息:\n"
        "• Telegram 連結 (https://t.me/...)\n"
        "• 轉發的圖片或影片\n\n"
        "💡 提示: 直接轉發訊息或貼上連結即可!"
    )


async def _process_download_requests(
    message_infos: list[MessageInfo], update: Update, message: Message
) -> None:
    """Process download requests for extracted message infos.

    Args:
        message_infos (List[MessageInfo]): Message information to process
        update (Update): The Telegram update object
        message (Message): The original message
    """
    try:
        # Send ONE reply message that will be edited throughout the process
        if len(message_infos) == 1:
            processing_msg = await message.reply_text("⏳ 正在處理下載請求...")
        else:
            processing_msg = await message.reply_text(
                f"⏳ 正在處理 {len(message_infos)} 個下載請求..."
            )

        # Add all tasks to batch queue using the same reply message
        for message_info in message_infos:
            await bot_instance.download_media_batch(
                message_info, update, processing_msg.message_id
            )

    except Exception as e:
        logfire.error("Error in message handling", error=str(e), _exc_info=True)
        await message.reply_text(f"❌ 處理訊息時發生錯誤: {e!s}")


async def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command.

    Args:
        update (Update): The Telegram update object
        context (CallbackContext): The callback context
    """
    welcome_message = (
        "🤖 **Telegram 媒體下載器** 歡迎你!\n\n"
        "📥 **使用方法:**\n"
        "• 直接轉發包含圖片或影片的訊息\n"
        "• 或者發送 Telegram 連結 (https://t.me/...)\n\n"
        "✨ **功能特色:**\n"
        "• 🚀 智能批量下載 (自動合併多個請求)\n"
        "• 📁 自動資料夾整理\n"
        "• ⚡ 即時下載狀態更新\n"
        "• 🔄 異步處理，提升效率\n\n"
        "💡 **小提示:** \n"
        "• 同時發送多個連結會自動批量處理\n"
        "• 相同來源的媒體會合併下載，速度更快!\n\n"
        "🔧 **可用命令:**\n"
        "• /start - 顯示此幫助訊息\n"
        "• /status - 查看下載隊列狀態"
    )

    if update.message:
        await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def status(update: Update, context: CallbackContext) -> None:
    """Handle the /status command to show download queue status.

    Args:
        update (Update): The Telegram update object
        context (CallbackContext): The callback context
    """
    if not update.message:
        return

    queue_size = len(bot_instance.batch_manager.download_queue)
    is_processing = bot_instance.batch_manager.processing

    status_message = (
        f"📊 **下載隊列狀態**\n\n"
        f"• 隊列中任務數量: {queue_size}\n"
        f"• 處理狀態: {'🟢 處理中' if is_processing else '🔴 空閒'}\n"
        f"• 批量大小: 20 個文件\n"
        f"• 批量超時: 3 秒"
    )

    if queue_size > 0:
        # Show some details about queued tasks
        recent_tasks = list(bot_instance.batch_manager.download_queue)[:3]
        status_message += "\n\n📋 **最近任務:**\n"
        for i, task in enumerate(recent_tasks, 1):
            time_ago = (datetime.now() - task.added_at).total_seconds()
            status_message += f"{i}. {task.message_info.post_sender} ({time_ago:.0f}s ago)\n"

        if queue_size > 3:
            status_message += f"... 及其他 {queue_size - 3} 個任務"

    await update.message.reply_text(status_message, parse_mode="Markdown")


async def error_handler(update: object, context: CallbackContext) -> None:
    """Handle errors that occur during bot operation.

    Args:
        update (object): The update that caused the error
        context (CallbackContext): The callback context containing error info
    """
    logfire.error("Bot encountered an error", error=str(context.error), _exc_info=True)

    # If we have a message to reply to, send an error message
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("❌ 系統發生錯誤，請稍後再試或聯繫管理員")


def main() -> None:
    """Main function to run the bot."""
    global bot_instance

    try:
        config = Config()

        # Create application
        application = Application.builder().token(config.token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(MessageHandler(filters.ALL, handle_message))

        # Add error handler
        application.add_error_handler(error_handler)

        logfire.info("Starting Telegram bot with batch download (20 files, 3s timeout)")

        # Run the bot
        application.run_polling(
            allowed_updates=["message"],  # Only process messages
            drop_pending_updates=True,  # Drop old updates on restart
        )

    except Exception as e:
        logfire.error("Failed to start bot", error=str(e), _exc_info=True)
        raise


if __name__ == "__main__":
    main()
