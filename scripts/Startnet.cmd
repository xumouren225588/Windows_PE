@echo off
echo 正在启动自动部署环境...
wpeinit

:: 启动部署脚本
start cmd /k "X:\Deploy\deploy.cmd"

:: 保持窗口打开
cmd /k
