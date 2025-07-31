#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试进度条功能
"""

import sys
import os
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from MaxStylePanelQt import MaxStylePanelQt

class ProgressBarTest(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # 创建主窗口
        self.main_window = MaxStylePanelQt()
        self.main_window.show()
        
        # 创建测试按钮
        test_button = QtWidgets.QPushButton("测试进度条")
        test_button.clicked.connect(self.test_progress)
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #3da9fc;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2176c1;
            }
        """)
        
        # 将测试按钮添加到主窗口
        self.main_window.layout().addWidget(test_button)
        
    def test_progress(self):
        """测试进度条功能"""
        print("开始测试进度条...")
        
        # 显示进度条
        self.main_window.show_task_progress(True)
        self.main_window.update_task_progress(0, "开始测试...")
        
        # 模拟进度更新
        progress = 0
        def update_progress():
            nonlocal progress
            progress += 10
            if progress <= 100:
                self.main_window.update_task_progress(progress, f"测试进度: {progress}%")
                QTimer.singleShot(500, update_progress)  # 500ms后再次更新
            else:
                # 测试完成，隐藏进度条
                QTimer.singleShot(1000, lambda: self.main_window.show_task_progress(False))
        
        # 开始进度更新
        QTimer.singleShot(100, update_progress)

def main():
    app = ProgressBarTest(sys.argv)
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 