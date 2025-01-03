@echo off
:: 設置命令行編碼為 UTF-8
chcp 65001
setlocal enabledelayedexpansion

rye sync
@REM rye run main
start powershell -NoExit -Command "rye run main"
