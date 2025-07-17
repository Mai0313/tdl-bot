<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

⚠️ **IMPORTANT**: After making any code changes, adding features, or updating functionality, you MUST update .github/copilot-instructions.md to reflect the current project state and capabilities.

# Project Background

This is a Telegram bot designed to download media files (images, videos) from Telegram messages. The bot can process both direct Telegram URLs and forwarded media messages, automatically organizing downloaded content into structured folders.

# Project Structure / Features

## Core Components

- **Telegram Bot (`src/bot.py`)**: Main bot implementation with enhanced message handling, error management, and user feedback
- **TDL Manager (`src/tdl/processor.py`)**: Wrapper for TDL (Telegram Downloader) binary with cross-platform support
- **Configuration (`src/utils/config.py`)**: Pydantic-based configuration management for Telegram API credentials
- **Binary Support**: Cross-platform TDL binaries for Windows and Linux

## Bot Features

- **URL Processing**: Handles direct Telegram URLs (https://t.me/channel/message_id)
- **Forwarded Media**: Processes forwarded images and videos with metadata extraction
- **Smart Folder Organization**: Creates organized folder structure based on channel and message ID
- **Real-time Feedback**: Provides processing status updates and download completion notifications
- **Error Handling**: Comprehensive error handling with user-friendly error messages
- **Logging**: Detailed logging using logfire for debugging and monitoring

## Technical Architecture

- **Pydantic Models**: Type-safe data models for message information and configuration
- **Async/Await**: Full asynchronous operation for responsive bot performance
- **Cross-platform**: Support for Windows and Linux environments
- **Modular Design**: Clean separation of concerns with dedicated classes for different functionalities

## Supported Message Types

1. **Direct URLs**: `https://t.me/username/message_id`
2. **Forwarded Media**: Images and videos forwarded from channels/chats
3. **Command Handling**: `/start` command with comprehensive usage instructions

## File Organization

```
data/
├── channel1_message1/    # Downloaded content organized by source
├── channel2_message2/
└── ...
```

# Rule Sheet

## Coding Style

- Follow `ruff-check` and `ruff-format` for code style and formatting using `pre-commit` hooks.
- Follow PEP 8 naming conventions:
    - snake_case for functions and variables
    - PascalCase for classes
    - UPPER_CASE for constants
- Follow the Python version specified in the `pyproject.toml` or `.python-version` file.
- Use pydantic model, and all pydantic models should include `Field`, and `description` should be included.
- Maximum line length of 99 characters
- Use absolute imports over relative imports
- Use `pytest` for testing, and all tests should be placed in the `tests/` directory

## Telegram Bot Specific Guidelines

- Use async/await for all bot operations
- Implement comprehensive error handling with user-friendly messages
- Provide real-time status updates to users during long operations
- Use Pydantic models for data validation and type safety
- Include detailed logging with logfire for debugging and monitoring
- Separate business logic into dedicated classes (e.g., TelegramBot class)
- Handle both Chinese and English user interactions gracefully

## Error Handling Best Practices

- Always catch specific exceptions rather than bare except clauses
- Provide meaningful error messages to users in Chinese
- Log detailed error information for debugging
- Implement graceful degradation when possible
- Use Optional types for values that might not exist

### Example

```python
from pydantic import BaseModel, Field
from typing import Optional


class MessageInfo(BaseModel):
    """Information extracted from a Telegram message.

    Attributes:
        post_id (str): The ID of the post
        post_sender (str): The sender username
    """

    post_id: str = Field(..., description="The ID of the post")
    post_sender: str = Field(..., description="The sender username")


async def safe_operation(update: Update) -> Optional[str]:
    """Example safe operation with proper error handling.

    Args:
        update (Update): The Telegram update object

    Returns:
        Optional[str]: Result of the operation or None if failed
    """
    try:
        # Perform operation
        result = await some_async_operation()
        return result
    except SpecificException as e:
        logfire.error("Operation failed", error=str(e))
        await update.message.reply_text("❌ 操作失敗，請稍後再試")
        return None
```

## Type Hints

- Use type hints for all function parameters and returns
- Use `TypeVar` for generic types
- Use `Protocol` for duck typing
- Use `Optional` for nullable values
- Import types from `typing` module when needed

## Documentation

- Use Google-style docstrings
- All documentation should be in English
- Use proper inline comments for better mkdocs support
- Document environment setup
- Include examples in docstrings when helpful

## Dependencies

- Use `uv` for dependency management
- Separate dev dependencies by adding `--dev` flag when adding dependencies
    - Production:
        - Add Dependencies: `uv add <package>`
        - Remove Dependencies: `uv remove <package>`
    - Development:
        - Add Dependencies: `uv add <package> --dev`
        - Remove Dependencies: `uv remove <package> --dev`
- Regularly update dependencies

## Bot Configuration

- Use environment variables for sensitive configuration (API tokens, keys)
- Validate configuration using Pydantic models
- Provide clear error messages for missing configuration
- Support both development and production environments
