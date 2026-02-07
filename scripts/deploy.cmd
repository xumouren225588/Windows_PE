@echo off
chcp 65001 >nul
title Windows 自动部署系统
color 0A

echo ========================================
echo    Windows 自动部署系统
echo    启动时间: %date% %time%
echo ========================================
echo.

:: 初始化 WinPE 环境
echo [1/5] 正在初始化 WinPE 环境...
wpeutil UpdateBootInfo

:: 等待系统稳定
timeout /t 3 /nobreak >nul

:: 检查0号磁盘是否是U盘
echo [2/5] 检查磁盘类型...
cscript //nologo X:\Deploy\check_usb.vbs
if %errorlevel% neq 0 (
    echo [错误] 0号磁盘检测失败或不是本地磁盘！
    echo 请确保系统安装在正确的磁盘上。
    pause
    exit /b 1
)
echo [信息] 0号磁盘检测通过（IDE/SCSI接口）

:: 查找 update.zip
echo [3/5] 在所有盘符中查找 update.zip...
set "UPDATE_FILE="
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%d:\update.zip" (
        echo [发现] 找到 update.zip 位于 %%d:\
        set "UPDATE_FILE=%%d:\update.zip"
        set "UPDATE_DRIVE=%%d:"
        goto :found_update
    )
)

if not defined UPDATE_FILE (
    echo [错误] 未在任何盘符找到 update.zip！
    echo 请确保 update.zip 位于某个盘符的根目录下。
    pause
    exit /b 1
)

:found_update
echo [信息] 找到更新包: %UPDATE_FILE%

:: 询问用户确认
echo.
echo ========================================
echo    即将执行以下操作：
echo    1. 解压 part.txt 到 Ramdisk (X:\)
echo    2. 对 0号磁盘进行分区（GPT）
echo    3. 解压 update.zip 到数据盘
echo    4. 使用 DISM 安装系统镜像
echo    5. 使用 BCDBoot 修复引导
echo.
echo    目标磁盘: 0号磁盘 (PHYSICALDRIVE0)
echo    更新包: %UPDATE_FILE%
echo ========================================
echo.
set /p confirm="是否继续执行部署? (Y/N): "
if /I not "%confirm%"=="Y" (
    echo 用户取消操作，退出...
    exit /b 0
)

:: 创建 Ramdisk 并解压 part.txt
echo [4/5] 准备分区脚本...
echo 正在创建 Ramdisk...
wpeutil CreateRamDisk 1024 >nul 2>&1
if not exist R:\ (
    echo [警告] 无法创建 Ramdisk，使用 X:\ 代替
    set "RAMDISK=X:\Ramdisk"
) else (
    set "RAMDISK=R:"
)
mkdir %RAMDISK% 2>nul

:: 解压 part.txt 从 update.zip
echo 正在从 update.zip 提取 part.txt...
powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%UPDATE_FILE%' -DestinationPath '%RAMDISK%' -Force"
if not exist "%RAMDISK%\part.txt" (
    echo [错误] 在 update.zip 中未找到 part.txt！
    pause
    exit /b 1
)
echo [信息] part.txt 已解压到 %RAMDISK%\part.txt

:: 执行 diskpart 分区
echo.
echo [5/5] 正在对 0号磁盘进行分区...
echo 这将清除磁盘上的所有数据！
echo.
diskpart /s "%RAMDISK%\part.txt"
if %errorlevel% neq 0 (
    echo [错误] 分区操作失败！
    pause
    exit /b 1
)
echo [信息] 分区完成

:: 确定系统盘和数据盘
echo 正在查找数据分区...
for %%d in (D E F G H) do (
    if exist "%%d:\" (
        echo [信息] 发现分区 %%d:\
        set "DATA_DRIVE=%%d:"
        goto :found_data
    )
)
set "DATA_DRIVE=D:"

:found_data
echo [信息] 数据盘确定为: %DATA_DRIVE%

:: 解压 update.zip 到数据盘
echo 正在解压 update.zip 到 %DATA_DRIVE%\...
powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%UPDATE_FILE%' -DestinationPath '%DATA_DRIVE%\' -Force"
if %errorlevel% neq 0 (
    echo [错误] 解压失败！
    pause
    exit /b 1
)
echo [信息] 解压完成

:: 查找 install.wim/esd/swm
echo 正在查找系统镜像...
set "IMAGE_FILE="
if exist "%DATA_DRIVE%\install.wim" set "IMAGE_FILE=%DATA_DRIVE%\install.wim"
if exist "%DATA_DRIVE%\install.esd" set "IMAGE_FILE=%DATA_DRIVE%\install.esd"
if exist "%DATA_DRIVE%\install.swm" set "IMAGE_FILE=%DATA_DRIVE%\install.swm"

if not defined IMAGE_FILE (
    echo [错误] 未找到 install.wim/esd/swm！
    pause
    exit /b 1
)
echo [信息] 找到系统镜像: %IMAGE_FILE%

:: 确定系统盘（通常是 C:）
set "SYSTEM_DRIVE=C:"

:: 使用 DISM 安装系统
echo.
echo ========================================
echo    正在安装 Windows 系统...
echo    目标: %SYSTEM_DRIVE%\
echo    镜像: %IMAGE_FILE%
echo ========================================
echo.

:: 格式化系统盘
format %SYSTEM_DRIVE% /FS:NTFS /Q /Y

:: 使用 DISM 应用镜像
echo 正在应用系统镜像，这可能需要几分钟...
dism /Apply-Image /ImageFile:"%IMAGE_FILE%" /Index:1 /ApplyDir:%SYSTEM_DRIVE%\
if %errorlevel% neq 0 (
    echo [错误] DISM 应用镜像失败！
    pause
    exit /b 1
)
echo [信息] 系统镜像应用完成

:: 使用 BCDBoot 修复引导
echo.
echo 正在修复系统引导...
bcdboot %SYSTEM_DRIVE%\Windows /s %SYSTEM_DRIVE% /f ALL
if %errorlevel% neq 0 (
    echo [警告] BCDBoot 执行可能出现问题，尝试备用方案...
    bcdboot %SYSTEM_DRIVE%\Windows /s %SYSTEM_DRIVE% /f UEFI
    bcdboot %SYSTEM_DRIVE%\Windows /s %SYSTEM_DRIVE% /f BIOS
)
echo [信息] 引导修复完成

:: 完成
echo.
echo ========================================
echo    部署完成！
echo    系统已安装到 %SYSTEM_DRIVE%\
echo    请移除安装介质并重启计算机
echo ========================================
echo.
pause
