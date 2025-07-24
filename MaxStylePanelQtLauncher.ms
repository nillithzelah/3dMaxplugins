macroScript MaxStylePanelQtLauncher
category:"StyleTools"
toolTip:"Max Style Panel (Qt)"
(
    on execute do
    (
        -- 尝试多个可能的路径
        local paths = #(
            -- 当前目录
            (getFilenamePath (getSourceFileName()) + "MaxStylePanelQt.py"),
            -- 用户宏目录
            (getDir #userMacros + "\\MaxStylePanelQt.py"),
            -- 指定的插件目录
            "D:\\3dsMax2022\\Plugins\\MaxStylePanel\\MaxStylePanelQt.py"
        )
        
        local scriptPath = undefined
        
        -- 检查哪个路径存在
        for p in paths do (
            if doesFileExist p then (
                scriptPath = p
                exit
            )
        )
        
        -- 执行找到的脚本
        if scriptPath != undefined then (
            python.ExecuteFile scriptPath
        ) else (
            messageBox "找不到MaxStylePanelQt.py文件。\n请确保文件位于以下位置之一：\n1. 与启动器脚本相同的目录\n2. 3ds Max的usermacros目录\n3. D:\\3dsMax2022\\Plugins\\MaxStylePanel\\" title:"错误" beep:true
        )
    )
)