"""Downloader module that wraps the tdl binary for downloading Telegram media."""

import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
import subprocess

logger = logging.getLogger(__name__)

# Timezone for Taipei (UTC+8)
_TPE_TZ = timezone(timedelta(hours=8))


def _get_tdl_binary_path() -> Path:
    """Get the absolute path to the tdl binary.

    Returns:
        Path: The absolute path to the tdl binary.
    """
    return Path(__file__).resolve().parent.parent / "binaries" / "tdl"


def _generate_download_dir(base_dir: str = "./data") -> Path:
    """Generate a timestamped download directory under the base directory.

    Args:
        base_dir: The base directory for downloads.

    Returns:
        Path: The generated download directory path.
    """
    timestamp = datetime.now(tz=_TPE_TZ).strftime("%Y%m%d_%H%M%S")
    download_dir = Path(base_dir) / timestamp
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


async def download_from_urls(urls: list[str], base_dir: str = "./data") -> tuple[Path, bool, str]:
    """Download media from Telegram message URLs using the tdl binary.

    Args:
        urls: A list of Telegram message URLs to download from.
        base_dir: The base directory for downloads.

    Returns:
        A tuple of (download_dir, success, message).
    """
    tdl_binary = _get_tdl_binary_path()
    if not tdl_binary.exists():
        return Path(base_dir), False, "tdl binary not found."

    download_dir = _generate_download_dir(base_dir)

    cmd: list[str] = [
        str(tdl_binary),
        "download",
        "--dir",
        str(download_dir),
        "--skip-same",
        "--rewrite-ext",
    ]

    for url in urls:
        cmd.extend(["--url", url])

    logger.info("Running tdl command: %s", " ".join(cmd))

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode().strip() if stdout else ""
        stderr_text = stderr.decode().strip() if stderr else ""

        if process.returncode == 0:
            # List downloaded files
            downloaded_files = list(download_dir.iterdir())
            file_names = [f.name for f in downloaded_files if f.is_file()]
            logger.info("Download completed. Files: %s", file_names)
            return download_dir, True, f"Downloaded {len(file_names)} file(s)."

        error_msg = stderr_text or stdout_text or "Unknown error"
        logger.error("tdl download failed (exit code %d): %s", process.returncode, error_msg)
        return download_dir, False, f"Download failed: {error_msg}"

    except Exception:
        logger.exception("Error running tdl download")
        return download_dir, False, "An unexpected error occurred during download."
