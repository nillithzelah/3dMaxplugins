-- 自动启动脚本 - 在3ds Max启动时自动加载Max Style Panel插件
-- 将此文件放在: %LOCALAPPDATA%\Autodesk\3dsMax\2025 - 64bit\ENU\scripts\Startup\

-- 延迟执行，确保3ds Max完全启动
callbacks.addScript #systemPostReset "loadMaxStylePanel()" id:#MaxStylePanelLoader

fn loadMaxStylePanel = (
    -- 等待一段时间确保系统稳定
    sleep 2
    
    -- 尝试多个可能的路径
    local paths = #(
        -- 用户宏目录 (推荐位置)
        (getDir #userMacros + "\\MaxStylePanelQt.py"),
        -- 启动脚本目录
        (getDir #userScripts + "\\Startup\\MaxStylePanelQt.py"),
        -- 插件目录
        (getDir #userScripts + "\\MaxStylePanel\\MaxStylePanelQt.py"),
        -- 指定的插件目录
        "D:\\3ds Max 2025\\scripts\\3dMaxplugins-master\\MaxStylePanelQt.py"
    )
    
    local scriptPath = undefined
    
    -- 检查哪个路径存在
    for p in paths do (
        if doesFileExist p then (
            scriptPath = p
            format "自动加载Max Style Panel插件: %\n" p
            exit
        )
    )
    
    -- 执行找到的脚本
    if scriptPath != undefined then (
        try (
            python.ExecuteFile scriptPath
            format "Max Style Panel插件已自动加载\n"
        ) catch (
            format "自动加载Max Style Panel插件失败: %\n" (getCurrentException())
        )
    ) else (
        format "未找到Max Style Panel插件文件，请检查安装\n"
    )
)

-- 立即尝试加载（如果系统已经准备好）
try (
    loadMaxStylePanel()
) catch (
    format "延迟加载Max Style Panel插件\n"
) 