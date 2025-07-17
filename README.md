<center>

# Telegram Downloader Bot

[![python](https://img.shields.io/badge/-Python_3.10_%7C_3.11_%7C_3.12-blue?logo=python&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![uv](https://img.shields.io/badge/-uv_dependency_management-2C5F2D?logo=python&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![tests](https://github.com/Mai0313/tdl-bot/actions/workflows/test.yml/badge.svg)](https://github.com/Mai0313/tdl-bot/actions/workflows/test.yml)
[![code-quality](https://github.com/Mai0313/tdl-bot/actions/workflows/code-quality-check.yml/badge.svg)](https://github.com/Mai0313/tdl-bot/actions/workflows/code-quality-check.yml)
[![codecov](https://codecov.io/gh/Mai0313/tdl-bot/branch/master/graph/badge.svg)](https://codecov.io/gh/Mai0313/tdl-bot)
[![license](https://img.shields.io/badge/License-MIT-green.svg?labelColor=gray)](https://github.com/Mai0313/tdl-bot/tree/master?tab=License-1-ov-file)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Mai0313/tdl-bot/pulls)
[![contributors](https://img.shields.io/github/contributors/Mai0313/tdl-bot.svg)](https://github.com/Mai0313/tdl-bot/graphs/contributors)

</center>

🤖 **An intelligent Telegram bot for downloading media files with advanced batch processing capabilities**

**Other Languages**: [English](README.md) | [中文](README_cn.md)

## ✨ Features

### 🚀 **Smart Batch Download System**

- **Intelligent Batching**: Automatically groups multiple download requests for optimal performance
- **Configurable Batch Size**: Customize batch size (1-20 URLs) and timeout settings
- **Efficient Processing**: Reduces download time by combining multiple requests
- **Real-time Status**: Live updates on download progress and queue status

### � **Media Download Capabilities**

- **URL Support**: Direct Telegram links (https://t.me/channel/message_id)
- **Forwarded Media**: Automatic handling of forwarded images and videos
- **Smart Organization**: Organized folder structure based on channel and message ID
- **Cross-platform**: Support for Windows and Linux environments

### 🛠️ **Technical Features**

- **Async Processing**: Full asynchronous operation for responsive performance
- **Type Safety**: Pydantic models for data validation and type safety
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Detailed logging with logfire for debugging and monitoring

### � **Configuration & Management**

- **Environment Variables**: Easy configuration through .env files
- **Status Command**: `/status` command to monitor download queue
- **Graceful Degradation**: Continues operation even with partial failures
- **Queue Management**: Smart queue processing with timeout handling
- **Release automation**: Semantic versioning and release drafting
- **Auto-labeling**: Intelligent PR categorization

### 📚 **Documentation**

- **MkDocs Material**: Beautiful, responsive documentation
- **Auto-generation**: Scripts to generate docs from code and notebooks
- **API documentation**: Automatic API reference generation
- **Blog support**: Built-in blog functionality for project updates

### 🤖 **Automation Scripts**

- **Project initialization**: `scripts/initpyrepo.go` for creating personalized projects
- **Documentation generation**: `scripts/gen_docs.py` for auto-generating documentation
- **Makefile commands**: Common development tasks automated

## 🚀 Quick Start

### Prerequisites

1. Python 3.10, 3.11, or 3.12
2. [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
3. Telegram Bot Token from [@BotFather](https://telegram.me/BotFather)
4. Telegram API credentials from [my.telegram.org](https://my.telegram.org/auth)

### Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/Mai0313/tdl-bot.git
    cd tdl-bot
    ```

2. **Install dependencies**

    ```bash
    make uv-install  # Install uv if not already installed
    uv sync          # Install project dependencies
    ```

3. **Configure environment**

    ```bash
    cp .env.example .env
    # Edit .env file with your Telegram credentials
    ```

4. **Run the bot**

    ```bash
    uv run python bot.py
    # or
    make run
    ```

### Configuration

Edit the `.env` file with your settings:

```bash
# Required: Telegram Bot Configuration
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Optional: Batch Download Configuration
BATCH_SIZE=5           # Max URLs per batch (1-20)
BATCH_TIMEOUT=3.0      # Batch processing timeout (0.5-30.0s)
DOWNLOAD_PATH=./data   # Download directory
```

### Usage

1. **Start a conversation** with your bot
2. **Send `/start`** to see the welcome message
3. **Send Telegram URLs** or **forward media messages**
4. **Check status** with `/status` command

#### Example Commands

```
/start  - Show welcome message and usage instructions
/status - View download queue status and configuration
```

#### Supported Message Types

- Direct Telegram URLs: `https://t.me/channel/message_id`
- Forwarded images and videos from any Telegram channel
- Multiple URLs sent in quick succession (automatic batching)

1. Run initial setup:
    ```bash
    make uv-install && uv sync && make format
    ```

## 📁 Project Structure

```
├── .devcontainer/          # VS Code Dev Container configuration
├── .github/
│   ├── workflows/          # CI/CD workflows
│   └── copilot-instructions.md
├── docker/                 # Docker configurations
├── docs/                   # MkDocs documentation
├── scripts/                # Automation scripts
├── src/
│   └── tdl-bot/      # Main package
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── Makefile               # Development commands
└── README.md
```

## 🛠️ Available Commands

```bash
# Development
make clean          # Clean autogenerated files
make format         # Run pre-commit hooks
make test           # Run all tests
make gen-docs       # Generate documentation

# Dependencies
make uv-install     # Install uv dependency manager
uv add <package>    # Add production dependency
uv add <package> --dev  # Add development dependency
```

## 🎯 What's Included

### CI/CD Workflows

- **Testing**: Multi-version Python testing on PRs
- **Code Quality**: Automated ruff checks and pre-commit validation
- **Documentation**: Automatic GitHub Pages deployment
- **Release**: Automated release drafting and changelog generation
- **Labeling**: Auto-labeling based on PR content

### Development Tools

- **ruff**: Fast Python linter and formatter
- **pytest**: Testing framework with coverage
- **pre-commit**: Git hooks for code quality
- **MkDocs**: Documentation generation
- **Docker**: Containerized development and deployment

### Project Templates

- **Python package**: Ready-to-use package structure
- **Configuration files**: All necessary config files included
- **Documentation**: Complete documentation setup
- **Testing**: Comprehensive test configuration

## 🎨 Customization Guide

### Project Name Customization

This template is designed for quick customization through simple global replacements:

1. **Replace package name**: Change all instances of `tdl-bot` to your project name (recommended: snake_case)
2. **Replace project title**: Change all instances of `Telegram Downloader Bot` to your project title (recommended: PascalCase)
3. **Update metadata**: Modify author, description, and other details in `pyproject.toml`

Example:

```bash
# If your project is called "awesome_project"
find . -type f -name "*.py" -o -name "*.md" -o -name "*.toml" | xargs sed -i 's/tdl-bot/awesome_project/g'
find . -type f -name "*.py" -o -name "*.md" -o -name "*.toml" | xargs sed -i 's/Telegram Downloader Bot/AwesomeProject/g'
```

## 🤝 Contributing

We welcome contributions! Please feel free to:

- Open issues for bugs or feature requests
- Submit pull requests for improvements
- Share your experience using this template

## 📖 Documentation

For detailed documentation, visit: [https://mai0313.github.io/tdl-bot/](https://mai0313.github.io/tdl-bot/)

## 👥 Contributors

[![Contributors](https://contrib.rocks/image?repo=Mai0313/tdl-bot)](https://github.com/Mai0313/tdl-bot/graphs/contributors)

Made with [contrib.rocks](https://contrib.rocks)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
