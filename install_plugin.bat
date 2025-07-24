@echo off
echo 正在安装Max Style Panel插件...

:: 创建目标目录（如果不存在）
set TARGET_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2022 - 64bit\ENU\usermacros
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: 复制Python文件
copy /Y "MaxStylePanelQt.py" "%TARGET_DIR%\"
echo Python脚本已复制到: %TARGET_DIR%\MaxStylePanelQt.py

:: 复制启动器脚本
set SCRIPTS_DIR=%LOCALAPPDATA%\Autodesk\3dsMax\2022 - 64bit\ENU\scripts\Startup
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
copy /Y "MaxStylePanelQtLauncher.ms" "%SCRIPTS_DIR%\"
echo 启动器脚本已复制到: %SCRIPTS_DIR%\MaxStylePanelQtLauncher.ms

echo.
echo 安装完成！请重启3ds Max。
pause