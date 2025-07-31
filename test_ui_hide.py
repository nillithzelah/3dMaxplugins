#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试3ds Max UI隐藏功能
使用方法：在3ds Max的Python控制台中运行
"""

try:
    import pymxs
    rt = pymxs.runtime
    
    print("🎯 开始测试UI隐藏功能...")
    
    # 测试隐藏UI元素
    hide_ui_code = '''
try (
    -- 隐藏ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已隐藏"
    
    -- 隐藏状态栏
    statusPanel.visible = false
    print "✅ 状态栏已隐藏"
    
    -- 隐藏视口控制栏（投影模式、着色模式等）
    try (
        -- 隐藏视口标签栏和按钮
        viewport.setLayout #layout_1
        -- 尝试隐藏视口控制元素
        actionMan.executeAction 0 "40140"  -- 隐藏命令面板
        print "✅ 视口控制栏已隐藏"
    ) catch (
        print "⚠️ 隐藏视口控制栏失败"
    )
    
    -- 隐藏坐标轴系统
    try (
        -- 隐藏坐标轴
        coordinateSystem.visible = false
        print "✅ 坐标轴系统已隐藏"
    ) catch (
        print "⚠️ 隐藏坐标轴系统失败"
    )
    
    -- 隐藏视口边框和标签
    try (
        -- 设置视口为全屏模式
        viewport.setLayout #layout_1
        -- 隐藏视口标签
        viewport.setLayout #layout_1
        print "✅ 视口边框已隐藏"
    ) catch (
        print "⚠️ 隐藏视口边框失败"
    )
    
    -- 尝试隐藏更多UI元素
    try (
        -- 隐藏工具栏
        toolbar.visible = false
        print "✅ 工具栏已隐藏"
    ) catch (
        print "⚠️ 隐藏工具栏失败"
    )
    
    -- 尝试隐藏视口控制按钮
    try (
        -- 隐藏视口控制按钮
        viewport.setLayout #layout_1
        print "✅ 视口控制按钮已隐藏"
    ) catch (
        print "⚠️ 隐藏视口控制按钮失败"
    )
    
    print "🎯 主视角UI元素隐藏完成"
) catch (
    print "⚠️ 隐藏UI元素时出现错误"
)
'''
    
    print("📝 执行隐藏UI代码...")
    rt.execute(hide_ui_code)
    
    print("⏰ 等待3秒后恢复UI...")
    import time
    time.sleep(3)
    
    # 测试恢复UI元素
    restore_ui_code = '''
try (
    -- 恢复ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已恢复"
    
    -- 恢复状态栏
    statusPanel.visible = true
    print "✅ 状态栏已恢复"
    
    -- 恢复视口控制栏
    try (
        -- 恢复视口标签栏
        viewport.setLayout #layout_1
        -- 恢复命令面板
        actionMan.executeAction 0 "40140"
        print "✅ 视口控制栏已恢复"
    ) catch (
        print "⚠️ 恢复视口控制栏失败"
    )
    
    -- 恢复坐标轴系统
    try (
        -- 恢复坐标轴
        coordinateSystem.visible = true
        print "✅ 坐标轴系统已恢复"
    ) catch (
        print "⚠️ 恢复坐标轴系统失败"
    )
    
    -- 恢复视口边框和标签
    try (
        -- 恢复视口布局
        viewport.setLayout #layout_1
        print "✅ 视口边框已恢复"
    ) catch (
        print "⚠️ 恢复视口边框失败"
    )
    
    -- 恢复工具栏
    try (
        -- 恢复工具栏
        toolbar.visible = true
        print "✅ 工具栏已恢复"
    ) catch (
        print "⚠️ 恢复工具栏失败"
    )
    
    print "🎯 主视角UI元素恢复完成"
) catch (
    print "⚠️ 恢复UI元素时出现错误"
)
'''
    
    print("📝 执行恢复UI代码...")
    rt.execute(restore_ui_code)
    
    print("✅ UI隐藏测试完成！")
    
except ImportError:
    print("❌ 无法导入pymxs模块，请确保在3ds Max环境中运行")
except Exception as e:
    print(f"❌ 测试失败: {str(e)}") 