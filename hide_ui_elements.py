#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
隐藏3ds Max四周UI元素的Python脚本
使用方法：在3ds Max的Python控制台中运行
"""

try:
    import pymxs
    rt = pymxs.runtime
    
    print("🎯 开始隐藏3ds Max四周UI元素...")
    
    # 隐藏ViewCube
    try:
        rt.viewport.setLayout(rt.name("layout_1"))
        print("✅ ViewCube已隐藏")
    except Exception as e:
        print(f"❌ 隐藏ViewCube失败: {str(e)}")
    
    # 隐藏状态栏
    try:
        rt.statusPanel.visible = False
        print("✅ 状态栏已隐藏")
    except Exception as e:
        print(f"❌ 隐藏状态栏失败: {str(e)}")
    
    # 隐藏命令面板（可选）
    # try:
    #     rt.actionMan.executeAction(0, "40140")
    #     print("✅ 命令面板已隐藏")
    # except Exception as e:
    #     print(f"❌ 隐藏命令面板失败: {str(e)}")
    
    # 隐藏工具栏（可选）
    # try:
    #     rt.toolbar.visible = False
    #     print("✅ 工具栏已隐藏")
    # except Exception as e:
    #     print(f"❌ 隐藏工具栏失败: {str(e)}")
    
    print("🎯 UI元素隐藏完成！")
    print("💡 提示：要恢复显示，请使用菜单栏的视图选项")
    
except ImportError:
    print("❌ 无法导入pymxs模块，请确保在3ds Max环境中运行")
except Exception as e:
    print(f"❌ 脚本执行失败: {str(e)}") 