@echo off
chcp 65001 >nul
title DeepPenny 依赖安装工具
setlocal enabledelayedexpansion

:: =============================================
::   DeepPenny 依赖安装工具
::   支持多镜像源自动切换与必装/可选组件管理
:: =============================================

:: ========== 镜像源配置（预设多个可靠镜像）==========
set MIRROR_COUNT=4
set MIRROR_1=https://pypi.tuna.tsinghua.edu.cn/simple
set MIRROR_2=https://mirrors.aliyun.com/pypi/simple/
set MIRROR_3=https://pypi.mirrors.ustc.edu.cn/simple/
set MIRROR_4=https://pypi.doubanio.com/simple/

:: ========== 必装组件定义 ==========
:: 格式: 名称 | pip规格 | 导入模块名 | 描述
set REQ_COUNT=2

set REQ_NAME_1=PyQt6
set REQ_SPEC_1=PyQt6^>=6.5.0
set REQ_MODULE_1=PyQt6
set REQ_DESC_1=核心 GUI 框架（必装，程序运行的基础）

set REQ_NAME_2=httpx
set REQ_SPEC_2=httpx^>=0.27.0
set REQ_MODULE_2=httpx
set REQ_DESC_2=HTTP 网络请求库（必装，用于 API 通信）

:: ========== 可选组件定义 ==========
set OPT_COUNT=3

set OPT_NAME_1=keyring
set OPT_SPEC_1=keyring^>=24.0.0
set OPT_MODULE_1=keyring
set OPT_DESC_1=安全凭证存储服务，用于加密保存 API 密钥等敏感信息

set OPT_NAME_2=pytest
set OPT_SPEC_2=pytest
set OPT_MODULE_2=pytest
set OPT_DESC_2=Python 测试框架，用于运行项目自动化测试用例

set OPT_NAME_3=psutil
set OPT_SPEC_3=psutil
set OPT_MODULE_3=psutil
set OPT_DESC_3=系统资源监控库，用于获取 CPU、内存等系统运行状态信息


:: =============================================
::                   主流程
:: =============================================

cls
echo =============================================
echo        DeepPenny 依赖安装工具
echo =============================================
echo.

:: ---------- 1. 检查 Python 环境 ----------
echo [环境检查] 正在检测 Python 环境...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境！
    echo   请先安装 Python（建议版本 3.9 或更高），安装地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo   [通过] Python 版本: %%i

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 pip 包管理器！
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('pip --version 2^>^&1') do echo   [通过] pip 版本: %%i
echo.

:: ---------- 2. 展示镜像源配置 ----------
echo [配置] 已预设以下国内镜像源：
echo.
for /l %%i in (1,1,%MIRROR_COUNT%) do (
    set "IDX=%%i"
    echo   镜像 !IDX!：!MIRROR_%%i!
)
echo.
echo   安装时将自动检测镜像可用性，按序切换（超时阈值：15 秒）。
echo   如果所有镜像均不可用，将自动回退至官方源（pypi.org）。
echo.
echo =============================================
echo.

:: ========== 步骤 1：必装组件检测与安装 ==========
echo [步骤 1/4] 检测必装组件...
echo.

set NEED_REQ_INSTALL=0

for /l %%i in (1,1,%REQ_COUNT%) do (
    set "NAME=!REQ_NAME_%%i!"
    set "MOD=!REQ_MODULE_%%i!"
    set "DESC=!REQ_DESC_%%i!"

    pip show !MOD! >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [已安装] !NAME! —— !DESC!
    ) else (
        echo   [未安装] !NAME! —— !DESC!
        set NEED_REQ_INSTALL=1
    )
)

echo.

if !NEED_REQ_INSTALL! equ 0 (
    echo   [完成] 所有必装组件均已就绪，无需安装。
) else (
    echo   [提示] 检测到有必装组件尚未安装，正在进行安装...
    echo   必装组件为程序运行所必需，将自动完成安装。
    echo.

    for /l %%i in (1,1,%REQ_COUNT%) do (
        set "NAME=!REQ_NAME_%%i!"
        set "SPEC=!REQ_SPEC_%%i!"
        set "MOD=!REQ_MODULE_%%i!"

        pip show !MOD! >nul 2>&1
        if !errorlevel! neq 0 (
            echo   ----------------------------------------
            echo   正在安装：!NAME!
            call :install_with_fallback "!SPEC!" "!NAME!"
            if !errorlevel! neq 0 (
                echo.
                echo   [错误] 必装组件 !NAME! 安装失败，无法继续。
                echo   请检查网络连接后重新运行本脚本。
                pause
                exit /b 1
            )
        )
    )
    echo   ----------------------------------------
    echo   [完成] 所有必装组件安装完毕。
)

echo.
echo =============================================
echo.

:: ========== 步骤 2：可选组件检测与交互式选择 ==========
echo [步骤 2/4] 检测可选组件...
echo.

set OPT_MISSING_COUNT=0
for /l %%i in (1,1,%OPT_COUNT%) do (
    set "NAME=!OPT_NAME_%%i!"
    set "MOD=!OPT_MODULE_%%i!"
    set "DESC=!OPT_DESC_%%i!"

    pip show !MOD! >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [已安装] !NAME! —— !DESC!
    ) else (
        echo   [未安装] !NAME! —— !DESC!
        set /a OPT_MISSING_COUNT+=1
    )
)

echo.

if !OPT_MISSING_COUNT! equ 0 (
    echo   [完成] 所有可选组件均已安装。
    set ANY_OPT_INSTALL=0
) else (
    echo   [说明] 可选组件非必需功能，可根据需要选择安装。
    echo   如果不需要，可以直接跳过，不影响程序基本运行。
    echo.

    set ANY_OPT_INSTALL=0
    set "OPT_INSTALL_LIST="

    for /l %%i in (1,1,%OPT_COUNT%) do (
        set "NAME=!OPT_NAME_%%i!"
        set "SPEC=!OPT_SPEC_%%i!"
        set "MOD=!OPT_MODULE_%%i!"
        set "DESC=!OPT_DESC_%%i!"

        pip show !MOD! >nul 2>&1
        if !errorlevel! neq 0 (
            echo   ----------------------------------------
            echo   可选组件：!NAME!
            echo   功能说明：!DESC!
            echo.
            choice /c YN /n /m "   [请选择] 是否安装 !NAME!？[Y=是 / N=否]："
            if !errorlevel! equ 1 (
                echo   用户选择：安装
                set ANY_OPT_INSTALL=1
                set "OPT_INSTALL_LIST=!OPT_INSTALL_LIST! %%i"
            ) else (
                echo   用户选择：跳过
            )
            echo.
        )
    )

    if !ANY_OPT_INSTALL! equ 1 (
        echo   ----------------------------------------
        echo   [开始] 正在安装选中的可选组件...
        echo.

        for %%j in (!OPT_INSTALL_LIST!) do (
            set "NAME=!OPT_NAME_%%j!"
            set "SPEC=!OPT_SPEC_%%j!"
            set "MOD=!OPT_MODULE_%%j!"

            pip show !MOD! >nul 2>&1
            if !errorlevel! neq 0 (
                echo   正在安装：!NAME!
                call :install_with_fallback "!SPEC!" "!NAME!"
            )
        )
        echo   ----------------------------------------
        echo   [完成] 可选组件安装完毕。
    ) else (
        echo   [跳过] 未选择安装任何可选组件。
    )
)

echo.
echo =============================================
echo.

:: ========== 步骤 3：验证安装结果 ==========
echo [步骤 3/4] 验证安装结果...
echo.

set VERIFY_FAILED=0

for /l %%i in (1,1,%REQ_COUNT%) do (
    set "NAME=!REQ_NAME_%%i!"
    set "MOD=!REQ_MODULE_%%i!"

    python -c "import !MOD!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [通过] !NAME! 导入成功
    ) else (
        echo   [失败] !NAME! 导入失败
        set VERIFY_FAILED=1
    )
)

for /l %%i in (1,1,%OPT_COUNT%) do (
    set "NAME=!OPT_NAME_%%i!"
    set "MOD=!OPT_MODULE_%%i!"

    pip show !MOD! >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import !MOD!" >nul 2>&1
        if !errorlevel! equ 0 (
            echo   [通过] !NAME! 导入成功
        ) else (
            echo   [警告] !NAME! 已安装但导入失败，可能存在兼容性问题
        )
    )
)

echo.

if !VERIFY_FAILED! equ 1 (
    echo   [警告] 部分必装组件验证未通过，程序可能无法正常运行。
    echo   建议重新运行本脚本，或手动排查相关组件的安装情况。
) else (
    echo   [验证] 所有已安装组件均验证通过。
)

echo.
echo =============================================
echo.

:: ========== 步骤 4：清理临时文件 ==========
echo [步骤 4/4] 清理临时文件...
echo.

:: 清理 pip 缓存
pip cache purge >nul 2>&1
echo   [清理] pip 全局缓存已清除

:: 清理 %TEMP% 下的 pip 临时目录
set "TEMP_PIP_CLEANED=0"
for /d %%d in ("%TEMP%\pip-*") do (
    rd /s /q "%%d" 2>nul
    set TEMP_PIP_CLEANED=1
)
for %%f in ("%TEMP%\pip-*.*") do (
    del /f /q "%%f" 2>nul
    set TEMP_PIP_CLEANED=1
)
if !TEMP_PIP_CLEANED! equ 1 (
    echo   [清理] %%TEMP%% 下的 pip 临时文件已清除
) else (
    echo   [状态] %%TEMP%% 下无 pip 临时文件
)

:: 清理 C:\Windows\Temp 下的 pip 临时目录
set "WIN_TEMP_PIP_CLEANED=0"
for /d %%d in ("C:\Windows\Temp\pip-*") do (
    rd /s /q "%%d" 2>nul
    set WIN_TEMP_PIP_CLEANED=1
)
for %%f in ("C:\Windows\Temp\pip-*.*") do (
    del /f /q "%%f" 2>nul
    set WIN_TEMP_PIP_CLEANED=1
)
if !WIN_TEMP_PIP_CLEANED! equ 1 (
    echo   [清理] C:\Windows\Temp 下的 pip 临时文件已清除
) else (
    echo   [状态] C:\Windows\Temp 下无 pip 临时文件
)

echo.
echo =============================================
echo.
echo   所有步骤执行完毕！
echo   运行命令：python main.py
echo.
echo =============================================
echo.

pause
exit /b 0


:: =============================================
::   辅助函数：带镜像源自动切换的安装
::   参数 %1：pip 包规格（如 PyQt6>=6.5.0）
::   参数 %2：显示名称（如 PyQt6）
::   返回：%errorlevel% = 0 成功，1 失败
:: =============================================
:install_with_fallback
set "PKG_SPEC=%~1"
set "PKG_NAME=%~2"
set "CURRENT=1"

:install_retry

if !CURRENT! gtr %MIRROR_COUNT% (
    echo.
    echo   [提示] 所有预设镜像源均无法连接。
    echo   正在尝试使用官方源（https://pypi.org）安装...
    echo.
    pip install "!PKG_SPEC!" --timeout 15 --retries 1
    if !errorlevel! equ 0 (
        echo   [成功] !PKG_NAME! 安装完成。
        exit /b 0
    )
    echo   [失败] !PKG_NAME! 安装失败，请检查网络或手动安装。
    exit /b 1
)

set "MIRROR_URL=!MIRROR_%CURRENT%!"
echo   镜像源 [!CURRENT!/%MIRROR_COUNT%]：!MIRROR_URL!

pip install "!PKG_SPEC!" -i !MIRROR_URL! --timeout 15 --retries 1
set "PIP_RESULT=!errorlevel!"

if !PIP_RESULT! equ 0 (
    echo   [成功] !PKG_NAME! 安装完成。
    exit /b 0
) else (
    echo   [切换] 镜像 !CURRENT! 连接失败（超时或拒绝连接），正在切换至下一个镜像源...
    echo.
    set /a CURRENT+=1
    goto install_retry
)
