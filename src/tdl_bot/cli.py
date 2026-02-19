"""CLI entry point for the Telegram Downloader Bot."""

import logging

from rich.logging import RichHandler

from tdl_bot.core.bot import create_bot
from tdl_bot.utils.config import Config


def _setup_logging() -> None:
    """Configure logging with RichHandler for pretty console output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def main() -> None:
    """Start the Telegram Downloader Bot."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    config = Config()
    logger.info("Starting TDL Bot...")
    logger.info("Download directory: ./data")

    bot = create_bot(config)
    bot.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
