#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的3ds Max UI隐藏测试
使用方法：在3ds Max的Python控制台中运行
"""

try:
    import pymxs
    rt = pymxs.runtime
    
    print("🎯 开始简单UI隐藏测试...")
    
    # 简单的隐藏UI代码
    simple_hide_code = '''
try (
    -- 隐藏ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已隐藏"
    
    -- 隐藏状态栏
    statusPanel.visible = false
    print "✅ 状态栏已隐藏"
    
    -- 隐藏坐标轴
    coordinateSystem.visible = false
    print "✅ 坐标轴已隐藏"
    
    print "🎯 简单UI隐藏完成"
) catch (
    print "⚠️ 隐藏UI时出现错误"
)
'''
    
    print("📝 执行隐藏UI代码...")
    rt.execute(simple_hide_code)
    
    print("⏰ 等待3秒后恢复UI...")
    import time
    time.sleep(3)
    
    # 简单的恢复UI代码
    simple_restore_code = '''
try (
    -- 恢复ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已恢复"
    
    -- 恢复状态栏
    statusPanel.visible = true
    print "✅ 状态栏已恢复"
    
    -- 恢复坐标轴
    coordinateSystem.visible = true
    print "✅ 坐标轴已恢复"
    
    print "🎯 简单UI恢复完成"
) catch (
    print "⚠️ 恢复UI时出现错误"
)
'''
    
    print("📝 执行恢复UI代码...")
    rt.execute(simple_restore_code)
    
    print("✅ 简单UI测试完成！")
    
except ImportError:
    print("❌ 无法导入pymxs模块，请确保在3ds Max环境中运行")
except Exception as e:
    print(f"❌ 测试失败: {str(e)}") 