@echo off
echo 正在卸载Max Style Panel插件...

:: 用户宏目录
set USER_MACROS_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\usermacros
if exist "%USER_MACROS_DIR%\MaxStylePanelQt.py" (
    del /Q "%USER_MACROS_DIR%\MaxStylePanelQt.py"
    echo 已删除: %USER_MACROS_DIR%\MaxStylePanelQt.py
)

:: 启动脚本目录
set STARTUP_SCRIPTS_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\scripts\Startup
if exist "%STARTUP_SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms" (
    del /Q "%STARTUP_SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms"
    echo 已删除: %STARTUP_SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms
)

if exist "%STARTUP_SCRIPTS_DIR%\auto_startup.ms" (
    del /Q "%STARTUP_SCRIPTS_DIR%\auto_startup.ms"
    echo 已删除: %STARTUP_SCRIPTS_DIR%\auto_startup.ms
)

:: 插件目录
set PLUGIN_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\scripts\MaxStylePanel
if exist "%PLUGIN_DIR%" (
    rmdir /S /Q "%PLUGIN_DIR%"
    echo 已删除插件目录: %PLUGIN_DIR%
)

:: UI配置文件
set UI_CONFIG_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\UI
if exist "%UI_CONFIG_DIR%\MaxStylePanel.mnu" (
    del /Q "%UI_CONFIG_DIR%\MaxStylePanel.mnu"
    echo 已删除菜单配置: %UI_CONFIG_DIR%\MaxStylePanel.mnu
)

echo.
echo ========================================
echo 卸载完成！
echo ========================================
echo.
echo 所有插件文件已清理。
echo 请重启3ds Max 2025以完成卸载。
echo.
pause 