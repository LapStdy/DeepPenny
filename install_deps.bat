@echo off
chcp 65001 >nul
title DeepPenny 依赖安装

set MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple

echo ========================================
echo   DeepPenny 依赖安装脚本
echo   镜像源: %MIRROR%
echo ========================================
echo.

:: ---------- 检查 Python ----------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo Python 版本: %%i

:: ---------- 检查 pip ----------
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 pip
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('pip --version 2^>^&1') do echo pip 版本: %%i
echo.

:: ---------- 核心依赖 ----------
echo [1/4] 检查核心依赖...
pip list --format=columns 2>nul | findstr /i "PyQt6" >nul
if %errorlevel% equ 0 (
    echo   PyQt6 已安装，跳过
) else (
    echo   安装 PyQt6...
    pip install "PyQt6>=6.5.0" -i %MIRROR%
)

pip list --format=columns 2>nul | findstr /i "httpx" >nul
if %errorlevel% equ 0 (
    echo   httpx 已安装，跳过
) else (
    echo   安装 httpx...
    pip install "httpx>=0.27.0" -i %MIRROR%
)

pip list --format=columns 2>nul | findstr /i "keyring" >nul
if %errorlevel% equ 0 (
    echo   keyring 已安装，跳过
) else (
    echo   安装 keyring...
    pip install "keyring>=24.0.0" -i %MIRROR%
)
echo.

:: ---------- 测试依赖 ----------
echo [2/4] 检查测试依赖...
pip list --format=columns 2>nul | findstr /i "pytest" >nul
if %errorlevel% equ 0 (
    echo   pytest 已安装，跳过
) else (
    echo   安装 pytest...
    pip install pytest -i %MIRROR%
)

pip list --format=columns 2>nul | findstr /i "psutil" >nul
if %errorlevel% equ 0 (
    echo   psutil 已安装，跳过
) else (
    echo   安装 psutil...
    pip install psutil -i %MIRROR%
)
echo.

:: ---------- 验证安装 ----------
echo [3/4] 验证安装...
python -c "import PyQt6; print('  PyQt6 OK')" 2>nul || echo  [警告] PyQt6 导入失败
python -c "import httpx;  print('  httpx  OK')" 2>nul || echo  [警告] httpx 导入失败
python -c "import keyring; print('  keyring OK')" 2>nul || echo  [警告] keyring 导入失败
echo.

:: ---------- 清理 pip 缓存 ----------
echo [4/4] 清理 pip 临时文件...
pip cache purge >nul 2>&1 && echo   pip 缓存已清理

if exist "%TEMP%\pip-*" (
    del /f /s /q "%TEMP%\pip-*" 2>nul
    echo   临时目录已清理
) else (
    2>nul
)
echo.

echo ========================================
echo   安装完成!
echo   运行: python main.py
echo ========================================
pause
