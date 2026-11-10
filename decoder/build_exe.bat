@echo off
chcp 65001 >nul
title vep 解码器 - Windows 打包脚本
echo ================================================
echo  大黄蜂云课堂 .vep 视频解码器 - 打包脚本
echo ================================================
echo.

REM 1. 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python。请先安装 Python 3.8 或更高版本，
    echo        安装时务必勾选 "Add Python to PATH"。
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已就绪

REM 2. 安装 PyInstaller
echo.
echo [1/3] 安装 PyInstaller ...
pip install pyinstaller -q

REM 3. 检查 ffmpeg.exe
echo.
set NOFFMPEG=0
if not exist "ffmpeg.exe" (
    echo [2/3] 当前目录未找到 ffmpeg.exe。
    echo.
    echo   请下载 Windows 静态版 ffmpeg（选 release essentials）：
    echo     https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    echo   解压后，把 ffmpeg-*-essentials_build\bin\ffmpeg.exe 复制到本目录。
    echo.
    echo   如果跳过这步，生成的 exe 运行时将依赖：
    echo   - 与 exe 同目录的 ffmpeg.exe，或
    echo   - 系统 PATH 里的 ffmpeg，或
    echo   - 启动时用 --ffmpeg 参数指定路径。
    echo.
    set /p "CHOICE=是否跳过 ffmpeg 打包继续? (y/n): "
    if /i not "%CHOICE%"=="y" (
        echo 已取消。请先放置 ffmpeg.exe 后重新运行。
        pause
        exit /b 1
    )
    set NOFFMPEG=1
) else (
    echo [2/3] 找到 ffmpeg.exe，将一起打包进 exe（单文件分发）
)

REM 4. 打包
echo.
echo [3/3] 打包为单文件 exe ...
if "%NOFFMPEG%"=="1" (
    pyinstaller --onefile --name "vep_decode" --console decode_vep.py
) else (
    pyinstaller --onefile --name "vep_decode" --console --add-binary "ffmpeg.exe;." decode_vep.py
)

echo.
echo ================================================
echo  打包完成！exe 位于 dist\vep_decode.exe
echo ================================================
echo.
echo 使用方法（拖拽即可）：
echo   把 .vep 文件直接拖到 vep_decode.exe 上，自动在同目录生成 *_解码.mp4
echo   或命令行：vep_decode.exe "课程.vep"
echo   批量：    vep_decode.exe *.vep
echo.
pause
