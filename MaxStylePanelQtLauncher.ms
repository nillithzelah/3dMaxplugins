macroScript MaxStylePanelQtLauncher
category:"StyleTools"
toolTip:"Max Style Panel (Qt)"
buttonText:"Max Style Panel"
(
    on execute do
    (
        -- 尝试多个可能的路径
        local paths = #(
            -- 用户宏目录 (推荐位置)
            (getDir #userMacros + "\\MaxStylePanelQt.py"),
            -- 启动脚本目录
            (getDir #userScripts + "\\Startup\\MaxStylePanelQt.py"),
            -- 插件目录
            (getDir #userScripts + "\\MaxStylePanel\\MaxStylePanelQt.py"),
            -- 当前目录
            (getFilenamePath (getSourceFileName()) + "MaxStylePanelQt.py"),
            -- 指定的插件目录
            "D:\\3ds Max 2025\\scripts\\3dMaxplugins-master\\MaxStylePanelQt.py"
        )
        
        local scriptPath = undefined
        
        -- 检查哪个路径存在
        for p in paths do (
            if doesFileExist p then (
                scriptPath = p
                format "找到脚本文件: %\n" p
                exit
            )
        )
        
        -- 执行找到的脚本
        if scriptPath != undefined then (
            try (
            python.ExecuteFile scriptPath
                format "成功加载Max Style Panel插件\n"
            ) catch (
                messageBox ("执行脚本时出错:\n" + getCurrentException()) title:"错误" beep:true
            )
        ) else (
            local errorMsg = "找不到MaxStylePanelQt.py文件。\n\n请确保文件位于以下位置之一：\n"
            for i = 1 to paths.count do (
                errorMsg += (i as string) + ". " + paths[i] + "\n"
            )
            errorMsg += "\n请运行install_plugin_2025.bat重新安装插件。"
            messageBox errorMsg title:"错误" beep:true
        )
    )
)