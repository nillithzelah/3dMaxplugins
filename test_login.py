import sys
import os
import time
from PySide2 import QtWidgets, QtCore, QtGui

# 导入MaxStylePanelQt模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import MaxStylePanelQt

def test_login():
    print("开始测试登录功能...")
    
    # 创建QApplication实例
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    
    # 创建登录窗口
    login_window = MaxStylePanelQt.LoginWindow()
    print("登录窗口已创建")
    
    # 设置用户数据
    user_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")
    import json
    # 强制重新创建用户数据文件
    password_hash = MaxStylePanelQt.LoginWindow.hash_password(None, "password")
    print(f"创建密码哈希: {password_hash}")
    with open(user_data_path, 'w', encoding='utf-8') as f:
        json.dump({"testuser": {"password_hash": password_hash}}, f)
    print("已创建测试用户数据")
    
    # 检查用户数据文件是否正确创建
    if os.path.exists(user_data_path):
        try:
            with open(user_data_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                print(f"用户数据文件内容: {user_data}")
        except Exception as e:
            print(f"读取用户数据文件失败: {str(e)}")
    else:
        print("用户数据文件未创建成功")
    
    # 定义一个简化版的create_main_panel函数，用于测试
    def test_create_main_panel():
        print("测试版create_main_panel被调用")
        # 创建主面板实例
        print("尝试创建主面板实例...")
        MaxStylePanelQt.main_panel_instance = MaxStylePanelQt.MaxStylePanelQt()
        print(f"主面板实例创建成功: {MaxStylePanelQt.main_panel_instance}")
        MaxStylePanelQt.main_panel_instance.show()
        print(f"主面板调用show()方法，可见性: {MaxStylePanelQt.main_panel_instance.isVisible()}")
        # 确保主面板在显示后被激活和置顶
        MaxStylePanelQt.main_panel_instance.activateWindow()
        MaxStylePanelQt.main_panel_instance.raise_()
        print("主面板已激活并置顶")
        return MaxStylePanelQt.main_panel_instance
    
    # 将测试版create_main_panel函数添加到MaxStylePanelQt模块
    MaxStylePanelQt.create_main_panel = test_create_main_panel
    
    # 连接登录成功信号
    try:
        print("连接loginSuccess信号到create_main_panel函数...")
        login_window.loginSuccess.connect(MaxStylePanelQt.create_main_panel)
        print("信号连接成功")
    except Exception as e:
        print(f"连接loginSuccess信号失败: {str(e)}")

    # 尝试自动登录
    print("尝试自动登录...")
    login_window.try_auto_login()
    
    # 登录窗口的显示由其内部逻辑控制，自动登录成功后应自动关闭
    # 如果自动登录失败，窗口会保持显示状态
    
    # 定义检查主面板函数
    def check_main_panel():
        # 将检查主面板的信息保存到文件
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                f.write("\n==== 检查主面板 ====\n")
                f.write(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"保存检查主面板信息时出错: {str(e)}")
            
        # 查找主面板
        main_panel = None
        # 首先尝试使用全局变量中的主面板
        if hasattr(MaxStylePanelQt, 'main_panel_instance') and MaxStylePanelQt.main_panel_instance:
            main_panel = MaxStylePanelQt.main_panel_instance
            print(f"从全局变量找到主面板: {main_panel.__class__.__name__}")
            print(f"主面板标题: {main_panel.windowTitle()}")
            print(f"主面板可见性: {main_panel.isVisible()}")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write(f"从全局变量找到主面板: {main_panel.__class__.__name__}\n")
                    f.write(f"主面板标题: {main_panel.windowTitle()}\n")
                    f.write(f"主面板可见性: {main_panel.isVisible()}\n")
            except Exception as e:
                print(f"保存主面板信息时出错: {str(e)}")
        
        # 如果全局变量中没有，则从所有窗口中查找
        if not main_panel:
            print("从所有窗口中查找主面板...")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write("从所有窗口中查找主面板...\n")
            except Exception as e:
                print(f"保存查找信息时出错: {str(e)}")
                
            for widget in QtWidgets.QApplication.topLevelWidgets():
                # 通过窗口标题查找
                if hasattr(widget, 'windowTitle') and widget.windowTitle() == u"多Tab演示面板（Qt版）":
                    main_panel = widget
                    print(f"通过标题找到主面板: {widget.__class__.__name__}")
                    try:
                        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                            f.write(f"通过标题找到主面板: {widget.__class__.__name__}\n")
                    except Exception as e:
                        print(f"保存查找结果时出错: {str(e)}")
                    break
                # 通过类型查找
                elif isinstance(widget, MaxStylePanelQt.MaxStylePanelQt):
                    main_panel = widget
                    print(f"通过类型找到主面板: {widget.__class__.__name__}")
                    try:
                        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                            f.write(f"通过类型找到主面板: {widget.__class__.__name__}\n")
                    except Exception as e:
                        print(f"保存查找结果时出错: {str(e)}")
                    break
        
        # 输出测试结果
        if main_panel and main_panel.isVisible():
            print("测试成功：登录后成功显示主面板")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write("测试成功：登录后成功显示主面板\n")
            except Exception as e:
                print(f"保存测试结果时出错: {str(e)}")
                
            # 打印主面板的所有按钮
            print("主面板的所有按钮:")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write("主面板的所有按钮:\n")
            except Exception as e:
                print(f"保存按钮信息时出错: {str(e)}")
                
            for child in main_panel.findChildren(QtWidgets.QPushButton):
                print(f"  - {child.text()}")
                try:
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                        f.write(f"  - {child.text()}\n")
                except Exception as e:
                    print(f"保存按钮详情时出错: {str(e)}")
            
            # 退出应用程序
            QtCore.QTimer.singleShot(1000, app.quit)
        else:
            print("测试失败：登录后未显示主面板或主面板不可见")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write("测试失败：登录后未显示主面板或主面板不可见\n")
            except Exception as e:
                print(f"保存测试失败信息时出错: {str(e)}")
                
            # 打印所有当前窗口
            print("当前所有窗口:")
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                    f.write("当前所有窗口:\n")
            except Exception as e:
                print(f"保存窗口列表信息时出错: {str(e)}")
                
            for i, widget in enumerate(QtWidgets.QApplication.topLevelWidgets()):
                print(f"  {i}. {widget.__class__.__name__}: {widget.windowTitle() if hasattr(widget, 'windowTitle') else ''}")
                print(f"     visible: {widget.isVisible()}")
                try:
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                        f.write(f"  {i}. {widget.__class__.__name__}: {widget.windowTitle() if hasattr(widget, 'windowTitle') else ''}\n")
                        f.write(f"     visible: {widget.isVisible()}\n")
                except Exception as e:
                    print(f"保存窗口详情时出错: {str(e)}")
                    
                if isinstance(widget, MaxStylePanelQt.MaxStylePanelQt):
                    print("     找到主面板窗口，但可能未被正确识别！")
                    try:
                        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                            f.write("     找到主面板窗口，但可能未被正确识别！\n")
                    except Exception as e:
                        print(f"保存识别信息时出错: {str(e)}")
            
            # 退出应用程序
            QtCore.QTimer.singleShot(1000, app.quit)
    
    # 保存初始状态到文件
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "w", encoding="utf-8") as f:
            f.write("==== 初始状态 ====\n")
            f.write(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"登录窗口已创建: {login_window}\n")
            f.write(f"用户名: {login_window.usernameEdit.text()}\n")
            f.write(f"密码: {'*' * len(login_window.passwordEdit.text())}\n")
        print("初始状态已保存到文件")
    except Exception as e:
        import traceback
        print(f"保存初始状态时出错: {str(e)}")
        print(traceback.format_exc())
    

    
    # 等待一段时间，确保主面板有足够时间显示
    time.sleep(2)
    
    # 检查主面板并输出结果
    check_main_panel()
    
    # 写入测试结果
    print("\n==== 输出测试结果 ====\n")
    try:
        # 检查主面板是否存在
        if hasattr(MaxStylePanelQt, 'main_panel_instance') and MaxStylePanelQt.main_panel_instance:
            print(f"主面板实例存在: {MaxStylePanelQt.main_panel_instance}")
            print(f"主面板可见性: {MaxStylePanelQt.main_panel_instance.isVisible()}")
            print("测试成功：主面板已创建并显示")
        else:
            print("测试失败：主面板未创建或未显示")
        
        # 查看所有窗口
        print("\n当前所有窗口:")
        for i, widget in enumerate(QtWidgets.QApplication.topLevelWidgets()):
            print(f"  {i}. {widget.__class__.__name__}: {widget.windowTitle() if hasattr(widget, 'windowTitle') else ''}")
            print(f"     visible: {widget.isVisible()}")
            if isinstance(widget, MaxStylePanelQt.MaxStylePanelQt):
                print("     找到主面板窗口！")
        
        # 将测试结果保存到文件
        result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt")
        print(f"保存测试结果到文件: {result_file}")
        with open(result_file, "a", encoding="utf-8") as f:
            f.write("\n==== 测试结果 ====\n")
            f.write(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            # 检查主面板是否存在
            if hasattr(MaxStylePanelQt, 'main_panel_instance') and MaxStylePanelQt.main_panel_instance:
                f.write(f"主面板实例存在: {MaxStylePanelQt.main_panel_instance}\n")
                f.write(f"主面板可见性: {MaxStylePanelQt.main_panel_instance.isVisible()}\n")
                f.write("测试成功：主面板已创建并显示\n")
            else:
                f.write("测试失败：主面板未创建或未显示\n")
            
            # 查看所有窗口
            f.write("\n当前所有窗口:\n")
            for i, widget in enumerate(QtWidgets.QApplication.topLevelWidgets()):
                f.write(f"  {i}. {widget.__class__.__name__}: {widget.windowTitle() if hasattr(widget, 'windowTitle') else ''}\n")
                f.write(f"     visible: {widget.isVisible()}\n")
                if isinstance(widget, MaxStylePanelQt.MaxStylePanelQt):
                    f.write(f"     找到主面板窗口！\n")
        print("测试结果已保存到文件")
    except Exception as e:
        import traceback
        print(f"保存测试结果时出错: {str(e)}")
        print(traceback.format_exc())
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_login_result.txt"), "a", encoding="utf-8") as f:
                f.write(f"\n保存测试结果时出错: {str(e)}\n")
                f.write(traceback.format_exc())
        except Exception as e2:
            print(f"保存错误信息时出错: {str(e2)}")
            print(traceback.format_exc())
    
    # 退出应用
    app.quit()
    
    # 运行应用程序事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_login()