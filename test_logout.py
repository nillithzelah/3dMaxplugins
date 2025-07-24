# -*- coding: utf-8 -*-
# 测试退出登录功能

import os
import sys
import time
from PySide2 import QtWidgets, QtCore, QtGui

# 导入主程序
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import MaxStylePanelQt

# 定义一个简化版的create_main_panel函数，用于测试
def test_create_main_panel():
    print("测试版create_main_panel被调用")
    # 创建主面板实例
    main_panel = MaxStylePanelQt.MaxStylePanelQt()
    main_panel.show()
    return main_panel

def test_logout():
    print("开始测试退出登录功能...")
    
    # 创建应用程序实例
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    
    # 将测试版create_main_panel函数添加到MaxStylePanelQt模块
    MaxStylePanelQt.create_main_panel = test_create_main_panel
    
    # 创建登录窗口
    login_window = MaxStylePanelQt.LoginWindow()
    login_window.show()
    
    # 模拟用户输入
    login_window.usernameEdit.setText("testuser")
    login_window.passwordEdit.setText("password")
    
    # 创建用户数据
    user_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")
    if not os.path.exists(user_data_path):
        import json
        with open(user_data_path, 'w', encoding='utf-8') as f:
            json.dump({"testuser": {"password_hash": MaxStylePanelQt.LoginWindow.hash_password(None, "password")}}, f)
        print("已创建测试用户数据")
    
    # 直接调用new_login方法，因为它会直接创建主面板
    print("直接调用new_login方法...")
    try:
        # 先设置用户数据
        user_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")
        if not os.path.exists(user_data_path):
            import json
            with open(user_data_path, 'w', encoding='utf-8') as f:
                password_hash = MaxStylePanelQt.LoginWindow.hash_password(None, "password")
                print(f"创建密码哈希: {password_hash}")
                json.dump({"testuser": {"password_hash": password_hash}}, f)
            print("已创建测试用户数据")
        
        # 设置全局用户名
        MaxStylePanelQt.current_username = "testuser"
        print(f"设置全局用户名: {MaxStylePanelQt.current_username}")
        
        # 直接创建主面板
        print("直接创建主面板...")
        try:
            # 创建主面板实例
            main_panel = MaxStylePanelQt.MaxStylePanelQt()
            
            # 设置用户名显示
            main_panel.usernameLabel.setText(MaxStylePanelQt.current_username)
            # 设置头像显示用户名首字母
            if MaxStylePanelQt.current_username and len(MaxStylePanelQt.current_username) > 0:
                main_panel.userAvatar.setText(MaxStylePanelQt.current_username[0].upper())
            
            # 显示主面板
            print("显示主面板...")
            main_panel.show()
            main_panel.raise_()
            
            # 设置全局变量
            MaxStylePanelQt.main_panel_instance = main_panel
            
            print(f"主面板创建结果: {main_panel}")
        except Exception as e:
            import traceback
            print(f"创建主面板过程中出错: {str(e)}")
            print(traceback.format_exc())
            sys.exit(1)
        
        # 关闭登录窗口
        login_window.close()
    except Exception as e:
        import traceback
        print(f"创建主面板过程中出错: {str(e)}")
        print(traceback.format_exc())
    
    # 等待主面板显示
    print("等待主面板显示...")
    time.sleep(2)  # 增加等待时间
    
    # 打印所有窗口
    print("当前所有窗口:")
    for i, widget in enumerate(QtWidgets.QApplication.allWidgets()):
        print(f"  {i}. {widget.__class__.__name__}: {widget.windowTitle()}")
        if hasattr(widget, 'objectName') and widget.objectName():
            print(f"     objectName: {widget.objectName()}")
        if hasattr(widget, 'isVisible'):
            print(f"     visible: {widget.isVisible()}")
    
    # 查找主面板
    main_panel = None
    # 首先尝试使用全局变量中的主面板
    if hasattr(MaxStylePanelQt, 'main_panel_instance') and MaxStylePanelQt.main_panel_instance:
        main_panel = MaxStylePanelQt.main_panel_instance
        print(f"从全局变量找到主面板: {main_panel.__class__.__name__}")
    
    # 如果全局变量中没有，则从所有窗口中查找
    if not main_panel:
        for widget in QtWidgets.QApplication.allWidgets():
            # 通过窗口标题查找
            if hasattr(widget, 'windowTitle') and widget.windowTitle() == u"多Tab演示面板（Qt版）":
                main_panel = widget
                print(f"通过标题找到主面板: {widget.__class__.__name__}")
                break
            # 通过类型查找
            elif hasattr(widget, '__class__') and widget.__class__.__name__ == 'MaxStylePanelQt':
                main_panel = widget
                print(f"通过类型找到主面板: {widget.__class__.__name__}")
                break
    
    if main_panel:
        # 测试退出登录功能
        print("测试退出登录功能...")
        # 查找退出登录按钮
        logout_button = None
        print("查找退出登录按钮...")
        for child in main_panel.findChildren(QtWidgets.QPushButton):
            print(f"按钮: {child.text()}")
            if child.text() == "退出登录":
                logout_button = child
                break
        
        if not logout_button:
            print("测试失败：未找到退出登录按钮")
            # 打印主面板的所有按钮
            print("主面板的所有按钮:")
            for child in main_panel.findChildren(QtWidgets.QPushButton):
                print(f"  - {child.text()}")
            sys.exit(1)
        
        # 模拟点击退出登录按钮
        print("模拟点击退出登录按钮...")
        logout_button.click()
        
        # 等待登录窗口重新显示
        print("等待登录窗口重新显示...")
        time.sleep(1)
        
        # 检查是否有登录窗口显示
        login_window_found = False
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, MaxStylePanelQt.LoginWindow) and widget.isVisible():
                login_window_found = True
                print(f"找到登录窗口: {widget}")
                break
        
        # 检查全局变量是否已重置
        if hasattr(MaxStylePanelQt, 'current_username'):
            print(f"全局用户名: {MaxStylePanelQt.current_username}")
        else:
            print("全局用户名不存在")
        
        if hasattr(MaxStylePanelQt, 'main_panel_instance'):
            print(f"全局主面板实例: {MaxStylePanelQt.main_panel_instance}")
        else:
            print("全局主面板实例不存在")
        
        if login_window_found:
            print("测试成功：退出登录后登录窗口已显示")
        else:
            print("测试失败：退出登录后未显示登录窗口")
            sys.exit(1)
    else:
        print("测试失败：未找到主面板")
        sys.exit(1)
    
    # 退出应用程序
    app.quit()

if __name__ == "__main__":
    test_logout()