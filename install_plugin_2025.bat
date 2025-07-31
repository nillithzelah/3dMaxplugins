@echo off
echo 正在安装Max Style Panel插件 (3ds Max 2025)...

:: 检测3ds Max 2025的安装路径
set MAX_2025_PATH=C:\Program Files\Autodesk\3ds Max 2025
if not exist "%MAX_2025_PATH%" (
    echo 错误：找不到3ds Max 2025安装路径
    echo 请检查3ds Max 2025是否正确安装在默认位置
    pause
    exit /b 1
)

:: 创建用户宏目录
set USER_MACROS_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\usermacros
if not exist "%USER_MACROS_DIR%" mkdir "%USER_MACROS_DIR%"

:: 复制Python文件到用户宏目录
copy /Y "MaxStylePanelQt.py" "%USER_MACROS_DIR%\"
echo Python脚本已复制到: %USER_MACROS_DIR%\MaxStylePanelQt.py

:: 创建启动脚本目录
set STARTUP_SCRIPTS_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\scripts\Startup
if not exist "%STARTUP_SCRIPTS_DIR%" mkdir "%STARTUP_SCRIPTS_DIR%"

:: 复制启动器脚本
copy /Y "MaxStylePanelQtLauncher.ms" "%STARTUP_SCRIPTS_DIR%\"
echo 启动器脚本已复制到: %STARTUP_SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms

:: 复制自动启动脚本
copy /Y "auto_startup.ms" "%STARTUP_SCRIPTS_DIR%\"
echo 自动启动脚本已复制到: %STARTUP_SCRIPTS_DIR%\auto_startup.ms

:: 创建插件目录（可选）
set PLUGIN_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\scripts\MaxStylePanel
if not exist "%PLUGIN_DIR%" mkdir "%PLUGIN_DIR%"
copy /Y "MaxStylePanelQt.py" "%PLUGIN_DIR%\"

:: 创建UI配置文件
set UI_CONFIG_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\UI
if not exist "%UI_CONFIG_DIR%" mkdir "%UI_CONFIG_DIR%"

:: 创建自定义菜单项
echo 正在创建自定义菜单...

:: 创建菜单配置文件
set MENU_FILE=%UI_CONFIG_DIR%\MaxStylePanel.mnu
echo macroScript MaxStylePanelQtLauncher category:"StyleTools" toolTip:"Max Style Panel (Qt)" ( on execute do ( python.ExecuteFile "%USER_MACROS_DIR%\MaxStylePanelQt.py" ) ) > "%MENU_FILE%"

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 安装位置：
echo - Python脚本: %USER_MACROS_DIR%\MaxStylePanelQt.py
echo - 启动器脚本: %STARTUP_SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms
echo - 菜单配置: %MENU_FILE%
echo.
echo 请按以下步骤操作：
echo 1. 重启3ds Max 2025
echo 2. 在菜单栏中找到 "StyleTools" 类别
echo 3. 点击 "Max Style Panel (Qt)" 启动插件
echo.
echo 如果插件没有自动加载，请手动执行：
echo python.ExecuteFile "%USER_MACROS_DIR%\MaxStylePanelQt.py"
echo.
pause 