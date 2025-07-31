-- 隐藏3ds Max四周UI元素的脚本
-- 使用方法：在3ds Max中运行此脚本

-- 隐藏ViewCube
try(
    viewport.setLayout #layout_1
    format "✅ ViewCube已隐藏\n"
)catch(
    format "❌ 隐藏ViewCube失败: %\n" (getCurrentException())
)

-- 隐藏状态栏
try(
    statusPanel.visible = false
    format "✅ 状态栏已隐藏\n"
)catch(
    format "❌ 隐藏状态栏失败: %\n" (getCurrentException())
)

-- 隐藏命令面板（可选）
-- try(
--     actionMan.executeAction 0 "40140"
--     format "✅ 命令面板已隐藏\n"
-- )catch(
--     format "❌ 隐藏命令面板失败: %\n" (getCurrentException())
-- )

-- 隐藏工具栏（可选）
-- try(
--     toolbar.visible = false
--     format "✅ 工具栏已隐藏\n"
-- )catch(
--     format "❌ 隐藏工具栏失败: %\n" (getCurrentException())
-- )

format "🎯 UI元素隐藏完成！\n"
format "💡 提示：要恢复显示，请使用菜单栏的视图选项\n" 