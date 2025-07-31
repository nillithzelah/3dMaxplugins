@echo off
REM 清空目标文件夹
@REM rd /s /q MaxStylePanel
rd /s /q PSStylePanel
rd /s /q SketchUpPanel

REM 复制各插件到对应子文件夹
xcopy /E /I /Y "D:\3dsMax2022\Plugins\MaxStylePanel\MaxStylePanel" MaxStylePanel
xcopy /E /I /Y "D:\ps 2020\Adobe Photoshop 2020\Required\CEP\extensions\dhzx.PSStylePanel" PSStylePanel
xcopy /E /I /Y "C:\Users\86012\AppData\Roaming\SketchUp\SketchUp 2022\SketchUp\Plugins\sketch_up" SketchUpPanel

echo 同步完成！
pause 