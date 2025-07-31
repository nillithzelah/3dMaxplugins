@echo off
echo 正在安装3ds Max插件所需的Python依赖...

REM 获取3ds Max的Python路径
set "PYTHON_PATH="
for /f "tokens=*" %%i in ('where python') do set "PYTHON_PATH=%%i"

if "%PYTHON_PATH%"=="" (
    echo 错误：找不到Python安装
    echo 请确保Python已正确安装并添加到PATH环境变量
    pause
    exit /b 1
)

echo 找到Python路径: %PYTHON_PATH%

REM 安装requests库
echo 正在安装requests库...
"%PYTHON_PATH%" -m pip install requests

if %errorlevel% neq 0 (
    echo 错误：安装requests库失败
    echo 请检查网络连接或手动安装
    pause
    exit /b 1
)

echo.
echo 安装完成！
echo 现在可以运行3ds Max插件了
pause 