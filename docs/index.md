<center>

# Telegram Downloader

[![python](https://img.shields.io/badge/-Python_3.8_%7C_3.9_%7C_3.10-blue?logo=python&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pytorch](https://img.shields.io/badge/PyTorch_2.0+-ee4c2c?logo=pytorch&logoColor=white)](https://pytorch.org/get-started/locally/)
[![lightning](https://img.shields.io/badge/-Lightning_2.0+-792ee5?logo=pytorchlightning&logoColor=white)](https://pytorchlightning.ai/)
[![hydra](https://img.shields.io/badge/Config-Hydra_1.3-89b8cd)](https://hydra.cc/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![tests](https://github.com/Mai0313/tdl-bot/actions/workflows/test.yml/badge.svg)](https://github.com/Mai0313/tdl-bot/actions/workflows/test.yml)
[![code-quality](https://github.com/Mai0313/tdl-bot/actions/workflows/code-quality-check.yml/badge.svg)](https://github.com/Mai0313/tdl-bot/actions/workflows/code-quality-check.yml)
[![codecov](https://codecov.io/gh/Mai0313/tdl-bot/branch/master/graph/badge.svg)](https://codecov.io/gh/Mai0313/tdl-bot)
[![license](https://img.shields.io/badge/License-MIT-green.svg?labelColor=gray)](https://github.com/Mai0313/tdl-bot/tree/master?tab=License-1-ov-file)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Mai0313/tdl-bot/pulls)
[![contributors](https://img.shields.io/github/contributors/Mai0313/tdl-bot.svg)](https://github.com/Mai0313/tdl-bot/graphs/contributors)

</center>

A clean template to kickstart your deep learning project 🚀⚡🔥
Click on [<kbd>Use this template</kbd>](https://github.com/Mai0313/tdl-bot/generate) to initialize new repository.

_Suggestions are always welcome!_

## Description

Telegram Downloader is a project designed to download media from Telegram channels and chats. It supports downloading photos, videos, and other files shared in Telegram messages.

## Features

- Download photos and videos from Telegram messages.
- Support for multiple file types.
- Integration with Gradio for a web-based interface.
- Logging and monitoring with Logfire.
- Configuration management with Pydantic.

## Installation

### Using PIP

```bash
# clone project
git clone https://github.com/Mai0313/tdl
mv tdl your-repo-name

# change directory
cd your-repo-name

# [OPTIONAL] create conda environment
conda create -n myenv python=3.9
conda activate myenv

# install requirements
pip install -r requirements.lock
```

### Using Rye

```bash
# clone project
git clone https://github.com/Mai0313/tdl
mv tdl your-repo-name

# change directory
cd your-repo-name

# install requirements
rye sync
```

## Usage

### Running the Bot

To start the Telegram bot, run:

```bash
python ./src/bot.py
```

### Running the Web Interface

To start the web interface using Gradio, run:

```bash
python ./src/web.py
```

## Configuration

Configuration is managed using Pydantic. You can set the configuration options in the

pyproject.toml

file under the `[tool.logfire]` section.

## Documentation

For more information, check the [Docs](https://mai0313.github.io/tdl/).

## License

This project is licensed under the MIT License. See the

LICENSE

file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

## Acknowledgements

- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Gradio](https://gradio.app/)
- [Logfire](https://docs.pydantic.dev/logfire/api/logfire/)
- [Ruff](https://github.com/astral-sh/ruff)
