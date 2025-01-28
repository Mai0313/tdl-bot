@echo off
:: 設置命令行編碼為 UTF-8
chcp 65001
setlocal enabledelayedexpansion

uv sync
@REM rye run main
start powershell -NoExit -Command "uv python ./src/main.py"
