#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3ds Max 插件 - 主程序
"""

import os
import sys
import json
import hashlib
import threading
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

# =========================
# API配置
# =========================
API_BASE_URL = "http://192.168.1.211:8200"
API_ENDPOINTS = {
    "login": "/api/login",
    "upload": "/api/upload/upImg", 
    "workflow": "/api/workFlow/OneWorkflows",
    "work_status": "/api/work/task",
    "work_list": "/api/work/list",
    "work_details": "/api/work/details",
    "work_cancel": "/api/workFlow/cancel",
    "work_delete": "/api/work/delete"
}

# 工作类型映射（按Tab分类）
WORK_TYPE_MAP = {
    # 室内设计
    "室内设计-彩平图": 100,
    "室内设计-毛坯房出图": 101,
    "室内设计-线稿出图": 102,
    "室内设计-白模渲染": 103,
    "室内设计-多风格（白模）": 104,
    "室内设计-多风格（线稿）": 105,
    "室内设计-风格转换": 106,
    "室内设计-360出图": 107,
    # 建筑规划
    "建筑规划-彩平图": 200,
    "建筑规划-现场出图": 201,
    "建筑规划-线稿出图": 202,
    "建筑规划-白模透视（精确）": 203,
    "建筑规划-白模透视（体块）": 204,
    "建筑规划-白模鸟瞰（精确）": 205,
    "建筑规划-白模鸟瞰（体块）": 206,
    "建筑规划-白天变夜景": 207,
    "建筑规划-亮化工程": 208,
    # 景观设计
    "景观设计-彩平图": 300,
    "景观设计-现场出图": 301,
    "景观设计-现场（局部）参考局部": 302,
    "景观设计-线稿出图": 303,
    "景观设计-白模（透视）": 304,
    "景观设计-白模（鸟瞰）": 305,
    "景观设计-白天转夜景": 306,
    "景观设计-亮化工程": 307,
    # 图像处理
    "图像处理-指定换材质": 400,
    "图像处理-修改局部": 401,
    "图像处理-AI去除万物": 402,
    "图像处理-AI去水印": 403,
    "图像处理-增加物体": 404,
    "图像处理-增加物体（指定物体）": 405,
    "图像处理-替换（产品）": 406,
    "图像处理-替换（背景天花）": 407,
    "图像处理-扩图": 408,
    "图像处理-洗图": 409,
    "图像处理-图像增强": 410,
    "图像处理-溶图（局部）": 411,
    "图像处理-放大出图": 412,
    "图像处理-老照片修复": 413
}

# =========================
# 全局变量
# =========================
current_username = None
login_dialog = None
main_panel_instance = None

# =========================
# 自动登录功能
# =========================

def get_auto_login_info():
    """获取自动登录信息"""
    auto_login_file = "auto_login.json"
    if os.path.exists(auto_login_file):
        try:
            with open(auto_login_file, 'r', encoding='utf-8') as f:
                auto_login_data = json.load(f)
            # 只要有用户名就返回数据，不检查auto_login字段
            if "username" in auto_login_data:
                return auto_login_data
        except Exception as e:
            print(f"读取自动登录信息失败: {str(e)}")
    return None

# =========================
# 上传图片控件（支持拖拽和点击上传）
# =========================
class ImageUploadWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, custom_height=None):
        super(ImageUploadWidget, self).__init__(parent)
        self.setAcceptDrops(True)  # 启用拖拽
        height = custom_height if custom_height else 240
        self.setFixedSize(260, height)
        # 设置控件样式（灰色虚线边框）
        self.setStyleSheet('''
            QWidget {
                background-color: #3a3a3a;
                border: 2px dashed #666;
                border-radius: 6px;
            }
        ''')
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # 图片显示区域
        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        icon_h = height - 60 if height > 80 else 40
        self.iconLabel.setFixedSize(240, icon_h)  # 填满上传框
        self.iconLabel.setStyleSheet("color: #bbb; font-size: 15px;")
        self.iconLabel.setText("")  # 不显示任何提示文字
        layout.addSpacing(8)  # 顶部只留8像素
        layout.addWidget(self.iconLabel)
        layout.addSpacing(8)  # 图片和文件名之间
        # 文件名显示区域
        self.fileNameLabel = QtWidgets.QLabel("")
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.fileNameLabel.setFixedHeight(20)
        self.fileNameLabel.setMaximumWidth(180)
        self.fileNameLabel.setStyleSheet("color: #fff; font-size: 13px; font-weight: bold; background: none; border: none;")
        fileNameRow = QtWidgets.QHBoxLayout()
        fileNameRow.addStretch(1)
        fileNameRow.addWidget(self.fileNameLabel)
        fileNameRow.addStretch(1)
        layout.addLayout(fileNameRow)
        # 文件名下不再加stretch，避免被挤压
        self.setLayout(layout)
        self.imagePath = None
        # 默认显示一个文件夹图标
        self.iconLabel.setPixmap(QtGui.QPixmap(":/qt-project.org/styles/commonstyle/images/dirclosed-128.png").scaled(240, icon_h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText("")

    # 鼠标点击事件，弹出文件选择对话框
    def mousePressEvent(self, event):
        self.openFileDialog()

    # 拖拽进入事件，高亮显示
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "background-color: #505080;")
        else:
            event.ignore()

    # 拖拽离开事件，恢复颜色
    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("background-color: #505080;", ""))

    # 拖拽释放事件，设置图片
    def dropEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("background-color: #505080;", ""))
        urls = event.mimeData().urls()
        if urls:
            filePath = urls[0].toLocalFile()
            self.setImage(filePath)

    # 打开文件选择对话框
    def openFileDialog(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)")
        if filePath:
            self.setImage(filePath)

    # 设置图片并显示文件名
    def setImage(self, filePath):
        if os.path.exists(filePath):
            pixmap = QtGui.QPixmap(filePath).scaled(
                self.iconLabel.width(), self.iconLabel.height(),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.iconLabel.setPixmap(pixmap)
            self.iconLabel.setText("")  # 清空提示
            self.fileNameLabel.setText(os.path.basename(filePath))
            self.imagePath = filePath
        else:
            self.iconLabel.clear()
            self.iconLabel.setText("")
            self.fileNameLabel.setText("")
            self.imagePath = None

# =========================
# 可点击的图片显示组件
# =========================
class ClickableImageView(QtWidgets.QWidget):
    """可点击的图片显示组件，支持点击放大"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setStyleSheet("""
            QWidget {
                background-color: #222; 
                border: 1px solid #444;
                border-radius: 8px;
            }
            QWidget:hover {
                border: 1px solid #3da9fc;
            }
        """)
        
        # 主布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 图片标签
        self.imageLabel = QtWidgets.QLabel()
        self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.imageLabel.setStyleSheet("background-color: transparent; border: none;")
        self.imageLabel.setText("未获取到视图")
        layout.addWidget(self.imageLabel)
        
        # 点击提示层（悬浮在图片上）
        self.overlayWidget = QtWidgets.QWidget(self)
        self.overlayWidget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 8px;
            }
        """)
        self.overlayWidget.hide()
        
        # 眼睛图标和提示文字
        overlayLayout = QtWidgets.QVBoxLayout(self.overlayWidget)
        overlayLayout.setAlignment(QtCore.Qt.AlignCenter)
        
        # 眼睛图标
        eyeIcon = QtWidgets.QLabel("👁️")
        eyeIcon.setAlignment(QtCore.Qt.AlignCenter)
        eyeIcon.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                background-color: transparent;
                border: none;
            }
        """)
        
        # 提示文字
        tipLabel = QtWidgets.QLabel("点击查看大图")
        tipLabel.setAlignment(QtCore.Qt.AlignCenter)
        tipLabel.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
                border: none;
                margin-top: 5px;
            }
        """)
        
        overlayLayout.addWidget(eyeIcon)
        overlayLayout.addWidget(tipLabel)
        
        # 鼠标事件
        self.setMouseTracking(True)
        self.imageLabel.setMouseTracking(True)
        
        # 图片路径
        self.currentImagePath = None
        
    def setImage(self, pixmap):
        """设置图片（默认显示点击提示）"""
        self.setImage(pixmap, showOverlay=True)
    
    def setImagePath(self, imagePath, showOverlay=True):
        """设置图片路径"""
        self.currentImagePath = imagePath
        if imagePath and os.path.exists(imagePath):
            pixmap = QtGui.QPixmap(imagePath)
            self.setImage(pixmap, showOverlay)
        else:
            self.imageLabel.setText("未获取到视图")
            self.overlayWidget.hide()
    
    def setImage(self, pixmap, showOverlay=True):
        """设置图片"""
        if pixmap and not pixmap.isNull():
            # 获取标签尺寸
            label_width = self.imageLabel.width()
            label_height = self.imageLabel.height()
            
            print(f"🔍 设置图片: 标签尺寸={label_width}x{label_height}, showOverlay={showOverlay}")
            
            if label_width > 0 and label_height > 0:
                # 缩放图片
                scaled = pixmap.scaled(label_width, label_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.imageLabel.setPixmap(scaled)
                self.imageLabel.setText("")
                
                # 设置是否应该显示悬浮层的标志
                self._shouldShowOverlay = showOverlay
                
                # 根据参数决定是否显示点击提示
                if showOverlay:
                    self.overlayWidget.show()
                    print(f"✅ 显示悬浮层，当前悬浮层可见: {self.overlayWidget.isVisible()}")
                else:
                    self.overlayWidget.hide()
                    print(f"✅ 隐藏悬浮层")
            else:
                # 如果标签尺寸为0，直接使用原图尺寸
                print(f"⚠️ 标签尺寸为0，使用原图尺寸: {pixmap.width()}x{pixmap.height()}")
                self.imageLabel.setPixmap(pixmap)
                self.imageLabel.setText("")
                
                # 设置是否应该显示悬浮层的标志
                self._shouldShowOverlay = showOverlay
                
                # 根据参数决定是否显示点击提示
                if showOverlay:
                    self.overlayWidget.show()
                    print(f"✅ 显示悬浮层，当前悬浮层可见: {self.overlayWidget.isVisible()}")
                else:
                    self.overlayWidget.hide()
                    print(f"✅ 隐藏悬浮层")
        else:
            self.imageLabel.setText("未获取到视图")
            self.overlayWidget.hide()
            print(f"❌ 图片为空或无效")
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        print(f"🔍 鼠标点击事件: 按钮={event.button()}, 图片路径={self.currentImagePath}, 悬浮层可见={self.overlayWidget.isVisible()}")
        
        # 只有当悬浮层显示时才允许点击（即只有生成的图片才能点击）
        if event.button() == QtCore.Qt.LeftButton and self.currentImagePath and self.overlayWidget.isVisible():
            print(f"✅ 触发点击放大功能")
            print(f"🔍 准备调用showFullImage")
            try:
                self.showFullImage()
                print(f"✅ showFullImage调用完成")
            except Exception as e:
                print(f"❌ showFullImage调用失败: {str(e)}")
                print(f"🔍 错误类型: {type(e).__name__}")
                import traceback
                print(f"🔍 完整错误堆栈: {traceback.format_exc()}")
                
                # 如果showFullImage失败，尝试直接打开
                print(f"🔄 尝试直接打开系统默认程序")
                try:
                    import os
                    import subprocess
                    import platform
                    
                    system = platform.system()
                    print(f"🔍 检测到操作系统: {system}")
                    print(f"🔍 图片路径: {self.currentImagePath}")
                    print(f"🔍 图片文件是否存在: {os.path.exists(self.currentImagePath)}")
                    
                    if system == "Windows":
                        print(f"🔍 尝试直接使用os.startfile")
                        os.startfile(self.currentImagePath)
                        print(f"✅ 直接打开成功")
                    else:
                        print(f"❌ 不支持的操作系统: {system}")
                except Exception as e2:
                    print(f"❌ 直接打开也失败: {str(e2)}")
                    print(f"🔍 错误类型: {type(e2).__name__}")
                    import traceback
                    print(f"🔍 完整错误堆栈: {traceback.format_exc()}")
        else:
            print(f"❌ 点击条件不满足: 左键={event.button() == QtCore.Qt.LeftButton}, 有图片路径={bool(self.currentImagePath)}, 悬浮层可见={self.overlayWidget.isVisible()}")
        
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        # 只有当悬浮层应该显示时才显示（即只有生成的图片才显示）
        if self.currentImagePath and hasattr(self, '_shouldShowOverlay') and self._shouldShowOverlay:
            self.overlayWidget.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.overlayWidget.hide()
        super().leaveEvent(event)
    
    def showFullImage(self):
        """显示完整图片"""
        print(f"🔍 showFullImage被调用")
        print(f"🔍 currentImagePath: {self.currentImagePath}")
        print(f"🔍 文件是否存在: {os.path.exists(self.currentImagePath) if self.currentImagePath else False}")
        
        if not self.currentImagePath or not os.path.exists(self.currentImagePath):
            print(f"❌ 图片路径无效或文件不存在")
            return
        
        print(f"✅ 图片路径有效，开始尝试打开")
        
        try:
            # 方案一：使用系统默认图片查看器
            print(f"🔍 尝试调用openWithSystemViewer")
            self.openWithSystemViewer()
            print(f"✅ openWithSystemViewer调用完成")
        except Exception as e:
            print(f"❌ 显示图片失败: {str(e)}")
            print(f"🔍 错误类型: {type(e).__name__}")
            import traceback
            print(f"🔍 完整错误堆栈: {traceback.format_exc()}")
            # 回退到自定义对话框
            try:
                print(f"🔄 回退到自定义对话框")
                self.openWithCustomDialog()
                print(f"✅ 自定义对话框打开成功")
            except Exception as e2:
                print(f"❌ 自定义对话框也失败: {str(e2)}")
                print(f"🔍 错误类型: {type(e2).__name__}")
                import traceback
                print(f"🔍 完整错误堆栈: {traceback.format_exc()}")
    
    def openWithSystemViewer(self):
        """使用系统默认图片查看器打开"""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            print(f"🔍 检测到操作系统: {system}")
            print(f"🔍 图片路径: {self.currentImagePath}")
            print(f"🔍 图片文件是否存在: {os.path.exists(self.currentImagePath)}")
            print(f"🔍 图片文件大小: {os.path.getsize(self.currentImagePath)} 字节")
            
            if system == "Windows":
                # 尝试多种Windows打开方式
                try:
                    # 方式1：使用os.startfile
                    print(f"🔍 尝试方式1: os.startfile")
                    os.startfile(self.currentImagePath)
                    print(f"✅ 方式1成功: 已使用系统默认程序打开")
                    return
                except Exception as e1:
                    print(f"❌ 方式1失败: {str(e1)}")
                    
                    try:
                        # 方式2：使用subprocess调用explorer
                        print(f"🔍 尝试方式2: explorer")
                        subprocess.run(["explorer", self.currentImagePath], check=True)
                        print(f"✅ 方式2成功: 已使用explorer打开")
                        return
                    except Exception as e2:
                        print(f"❌ 方式2失败: {str(e2)}")
                        
                        try:
                            # 方式3：使用subprocess调用默认程序
                            print(f"🔍 尝试方式3: start命令")
                            subprocess.run(["start", "", self.currentImagePath], shell=True, check=True)
                            print(f"✅ 方式3成功: 已使用start命令打开")
                            return
                        except Exception as e3:
                            print(f"❌ 方式3失败: {str(e3)}")
                            
                            # 所有方式都失败，抛出异常
                            raise Exception(f"所有Windows打开方式都失败: {str(e1)}, {str(e2)}, {str(e3)}")
                            
            elif system == "Darwin":  # macOS
                print(f"🔍 尝试使用macOS默认程序打开: {self.currentImagePath}")
                subprocess.run(["open", self.currentImagePath])
                print(f"✅ 已使用系统默认程序打开: {self.currentImagePath}")
            else:  # Linux
                print(f"🔍 尝试使用Linux默认程序打开: {self.currentImagePath}")
                subprocess.run(["xdg-open", self.currentImagePath])
                print(f"✅ 已使用系统默认程序打开: {self.currentImagePath}")
                
        except Exception as e:
            print(f"❌ 系统默认程序打开失败: {str(e)}")
            print(f"🔍 错误类型: {type(e).__name__}")
            print(f"🔍 详细错误信息: {e}")
            raise e
    
    def openWithCustomDialog(self):
        """使用自定义对话框打开"""
        try:
            dialog = ImageViewerDialog(self.currentImagePath, self)
            dialog.exec_()
        except Exception as e:
            print(f"❌ 自定义对话框打开失败: {str(e)}")
    
    def openWithSimpleDialog(self):
        """使用简单对话框打开（无全屏）"""
        try:
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("图片查看")
            dialog.setModal(True)
            
            # 设置对话框大小
            screen = QtWidgets.QApplication.primaryScreen()
            screenGeometry = screen.geometry()
            dialogWidth = int(screenGeometry.width() * 0.8)
            dialogHeight = int(screenGeometry.height() * 0.8)
            dialog.resize(dialogWidth, dialogHeight)
            
            # 创建布局
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # 创建图片标签
            imageLabel = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(self.currentImagePath)
            if not pixmap.isNull():
                # 缩放图片适应对话框
                scaledPixmap = pixmap.scaled(dialogWidth-50, dialogHeight-100, 
                                           QtCore.Qt.KeepAspectRatio, 
                                           QtCore.Qt.SmoothTransformation)
                imageLabel.setPixmap(scaledPixmap)
                imageLabel.setAlignment(QtCore.Qt.AlignCenter)
            
            # 创建关闭按钮
            closeButton = QtWidgets.QPushButton("关闭")
            closeButton.clicked.connect(dialog.close)
            
            layout.addWidget(imageLabel)
            layout.addWidget(closeButton)
            
            dialog.exec_()
        except Exception as e:
            print(f"❌ 简单对话框打开失败: {str(e)}")
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 重新调整悬浮层大小
        self.overlayWidget.setGeometry(0, 0, self.width(), self.height())


class ImageViewerDialog(QtWidgets.QDialog):
    """图片查看对话框"""
    
    def __init__(self, imagePath, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片查看")
        self.setModal(True)
        
        # 先设置布局，再设置全屏
        self.setupUI(imagePath)
        
        # 强制设置全屏显示（在布局设置之后）
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.showFullScreen()  # 确保全屏显示
        
        # 获取屏幕尺寸
        screen = QtWidgets.QApplication.primaryScreen()
        screenGeometry = screen.geometry()
        print(f"✅ 全屏显示，屏幕尺寸: {screenGeometry.width()}x{screenGeometry.height()}")
        
        # 延迟执行缩放，确保全屏设置生效
        QtCore.QTimer.singleShot(100, self.fitImageToView)
        QtCore.QTimer.singleShot(300, self.fitImageToView)
        QtCore.QTimer.singleShot(500, self.fitImageToView)
    
    def setupUI(self, imagePath):
        """设置UI布局"""
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #000;
                color: white;
            }
        """)
        
        # 主布局 - 图片占满整个屏幕
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        # 图片显示区域 - 使用QGraphicsView提供更好的缩放控制
        self.graphicsView = QtWidgets.QGraphicsView()
        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.graphicsView.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.graphicsView.setStyleSheet("""
            QGraphicsView {
                background-color: #000;
                border: none;
            }
        """)
        
        # 创建场景
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        
        # 加载并显示图片
        if os.path.exists(imagePath):
            pixmap = QtGui.QPixmap(imagePath)
            if not pixmap.isNull():
                # 创建图形项
                self.pixmapItem = self.scene.addPixmap(pixmap)
                print(f"✅ 图片加载成功，原始尺寸: {pixmap.width()}x{pixmap.height()}")
                
                # 设置场景矩形
                self.graphicsView.setSceneRect(self.pixmapItem.boundingRect())
                
                # 连接大小改变事件
                self.graphicsView.resizeEvent = self.onGraphicsViewResize
            else:
                print(f"❌ 图片数据无效")
        else:
            print(f"❌ 图片文件不存在: {imagePath}")
        
        # 顶部控制栏（悬浮）
        self.controlBar = QtWidgets.QWidget()
        self.controlBar.setFixedHeight(50)
        self.controlBar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border: none;
            }
        """)
        
        controlLayout = QtWidgets.QHBoxLayout(self.controlBar)
        controlLayout.setContentsMargins(20, 10, 20, 10)
        controlLayout.setSpacing(10)
        
        # 标题
        titleLabel = QtWidgets.QLabel("图片查看")
        titleLabel.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # 关闭按钮
        closeButton = QtWidgets.QPushButton("✕ 关闭")
        closeButton.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        closeButton.clicked.connect(self.close)
        
        controlLayout.addWidget(titleLabel)
        controlLayout.addStretch()
        controlLayout.addWidget(closeButton)
        
        # 添加到主布局
        mainLayout.addWidget(self.controlBar)
        mainLayout.addWidget(self.graphicsView)
        
        # 初始时隐藏控制栏
        self.controlBar.hide()
        
        # 添加鼠标事件处理
        self.graphicsView.mousePressEvent = self.onMousePress
        self.graphicsView.mouseDoubleClickEvent = self.onMouseDoubleClick
    
    def fitImageToView(self):
        """将图片适应到视图大小"""
        if hasattr(self, 'pixmapItem'):
            # 获取视图和场景的实际尺寸
            view_size = self.graphicsView.size()
            scene_rect = self.pixmapItem.boundingRect()
            
            print(f"🔍 视图尺寸: {view_size.width()}x{view_size.height()}")
            print(f"🔍 场景尺寸: {scene_rect.width()}x{scene_rect.height()}")
            
            # 如果视图尺寸为0，等待一下再试
            if view_size.width() <= 0 or view_size.height() <= 0:
                print("⚠️ 视图尺寸为0，延迟重试")
                QtCore.QTimer.singleShot(100, self.fitImageToView)
                return
            
            # 计算缩放比例
            scale_x = view_size.width() / scene_rect.width()
            scale_y = view_size.height() / scene_rect.height()
            scale = min(scale_x, scale_y)  # 保持宽高比
            
            print(f"🔍 计算缩放比例: scale_x={scale_x:.2f}, scale_y={scale_y:.2f}, 最终scale={scale:.2f}")
            
            # 重置变换
            self.graphicsView.resetTransform()
            
            # 应用缩放
            self.graphicsView.scale(scale, scale)
            
            # 居中显示
            self.graphicsView.centerOn(self.pixmapItem)
            
            # 强制更新
            self.graphicsView.viewport().update()
            
            print(f"✅ 图片已适应视图大小，缩放比例: {scale:.2f}")
            
            # 验证缩放结果
            transformed_rect = self.graphicsView.mapToScene(self.graphicsView.viewport().rect())
            print(f"🔍 变换后视图范围: {transformed_rect.width():.1f}x{transformed_rect.height():.1f}")
    
    def onGraphicsViewResize(self, event):
        """处理QGraphicsView大小改变事件"""
        if hasattr(self, 'pixmapItem'):
            self.fitImageToView()
        event.accept()
    
    def resizeEvent(self, event):
        """处理对话框大小改变事件"""
        super().resizeEvent(event)
        if hasattr(self, 'pixmapItem'):
            self.fitImageToView()
    
    def onMousePress(self, event):
        """鼠标点击事件 - 显示/隐藏控制栏"""
        if event.button() == QtCore.Qt.LeftButton:
            if self.controlBar.isVisible():
                self.controlBar.hide()
            else:
                self.controlBar.show()
        event.accept()
    
    def onMouseDoubleClick(self, event):
        """鼠标双击事件 - 退出全屏"""
        if event.button() == QtCore.Qt.LeftButton:
            self.close()
        event.accept()


# =========================
# 可折叠参数区域控件
# =========================
class CollapsibleWidget(QtWidgets.QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        # 标题按钮
        self.toggleButton = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self.toggleButton.setStyleSheet("""
            QToolButton {
                background: none;
                border: none;
                color: #fff;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                padding: 2px 0 0 16px; /* 左边距16px，与内容左对齐 */
            }
        """)
        self.toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
        self.toggleButton.clicked.connect(self.onToggle)

        # 内容区
        self.contentArea = QtWidgets.QWidget()
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)
        self.contentArea.setStyleSheet("background: none;")

        # 动画效果
        self.toggleAnimation = QtCore.QPropertyAnimation(self.contentArea, b"maximumHeight")
        self.toggleAnimation.setDuration(180)
        self.toggleAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(-2)  # 标题和内容区更贴合
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggleButton)
        layout.addWidget(self.contentArea)

    # 设置内容区的布局
    def setContentLayout(self, contentLayout):
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = 0
        expandedHeight = contentLayout.sizeHint().height()
        self.toggleAnimation.setStartValue(collapsedHeight)
        self.toggleAnimation.setEndValue(expandedHeight)

    # 点击展开/收起
    def onToggle(self, checked):
        if checked:
            self.toggleButton.setArrowType(QtCore.Qt.DownArrow)
            contentHeight = self.contentArea.layout().sizeHint().height()
            self.toggleAnimation.setEndValue(contentHeight)
            self.toggleAnimation.setDirection(QtCore.QAbstractAnimation.Forward)
            self.toggleAnimation.start()
        else:
            self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
            self.toggleAnimation.setDirection(QtCore.QAbstractAnimation.Backward)
            self.toggleAnimation.start()

# =========================
# 高级参数弹窗控件
# =========================
class AdvancedParamsPopup(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Popup)
        self.setStyleSheet('''
            QFrame {
                background: #222;
                border: 1px solid #3af;
                border-radius: 8px;
            }
        ''')
        self.setWindowFlags(QtCore.Qt.Popup)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        self.sliders = {}
        # 预设的高级参数
        advancedParams = [
            ("噪声强度", 0, 100, 30),
            ("细节层次", 0, 100, 50),
            ("色彩饱和度", 0, 100, 60),
            ("对比度", 0, 100, 45),
            ("锐化程度", 0, 100, 25)
        ]
        for paramName, minVal, maxVal, defaultVal in advancedParams:
            paramLayout = QtWidgets.QHBoxLayout()
            paramLabel = QtWidgets.QLabel(paramName)
            paramLabel.setStyleSheet("color: white; font-size: 13px; min-width: 80px;")
            paramSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            paramSlider.setMinimum(minVal)
            paramSlider.setMaximum(maxVal)
            paramSlider.setValue(defaultVal)
            paramSlider.setFixedWidth(120)
            paramSlider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #333;
                    height: 4px;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #3af;
                    width: 14px;
                    border-radius: 7px;
                }
                QSlider::sub-page:horizontal {
                    background: #3af;
                    border-radius: 2px;
                }
            """)
            paramValue = QtWidgets.QLineEdit(str(defaultVal))
            paramValue.setFixedWidth(40)
            paramValue.setAlignment(QtCore.Qt.AlignCenter)
            paramValue.setStyleSheet("background-color: #333; color: white; border: 1px solid #555;")
            # 滑块和输入框联动
            def createSliderCallback(slider, valueEdit):
                def sliderChanged(val):
                    valueEdit.setText(str(val))
                return sliderChanged
            def createValueCallback(slider, valueEdit):
                def valueChanged():
                    try:
                        val = int(valueEdit.text())
                        val = max(slider.minimum(), min(slider.maximum(), val))
                        slider.setValue(val)
                    except:
                        pass
                return valueChanged
            paramSlider.valueChanged.connect(createSliderCallback(paramSlider, paramValue))
            paramValue.editingFinished.connect(createValueCallback(paramSlider, paramValue))
            paramLayout.addWidget(paramLabel)
            paramLayout.addWidget(paramSlider)
            paramLayout.addWidget(paramValue)
            paramLayout.addStretch(1)
            layout.addLayout(paramLayout)
            self.sliders[paramName] = (paramSlider, paramValue)
        self.setLayout(layout)

# =========================
# 递归清理layout的函数，确保所有子控件和子layout都能被删除
# =========================
def clearLayout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                clearLayout(child_layout)

# =========================
# 每个Tab的内容区控件
# =========================
class TabContentWidget(QtWidgets.QWidget):
    MULTI_PROMPT_DEFAULTS = {
        "多风格（白模）": [
            "书房，现代风格，书桌",
            "卧室，现代风格",
            "客厅，现代风格"
        ],
        "多风格（线稿）": [
            "卧室，现代风格",
            "客厅，现代风格",
            "书房，现代风格"
        ]
    }
    PROMPT_DEFAULTS = {
        # 室内设计
        "彩平图": "彩平图，现代风格，客厅布局",
        "毛坯房出图": "客厅,复古法式风格，金属茶几，沙发，地毯，装饰品，阳台，极精细的细节，吊灯",
        "线稿出图": "卧室，现代风格，简约线条",
        "白模渲染": "卧室，现代风格，电脑，书，电脑椅",
        "多风格（白模）": "书房，现代风格，书桌",
        "多风格（线稿）": "卧室，现代风格",
        "风格转换": "客厅，中式风格，传统装饰",
        "360出图": "全景室内，360度视角",
        # 建筑规划
        "彩平图": "建筑彩平图，现代建筑设计",
        "现场出图": "建筑工地，现代风格，施工现场",
        "线稿出图": "建筑线稿，简约风格，结构清晰",
        "白模透视（精确）": "建筑白模，精确透视，细节建模",
        "白模透视（体块）": "建筑体块白模，鸟瞰视角",
        "白模鸟瞰（精确）": "建筑鸟瞰，精确建模，高空视角",
        "白模鸟瞰（体块）": "建筑鸟瞰，体块模型，简化结构",
        "白天变夜景": "夜景，灯光渲染，城市夜景",
        "亮化工程": "建筑亮化，灯光设计，夜景照明",
        # 景观设计
        "彩平图": "景观彩平图，现代景观设计",
        "现场出图": "景观现场，现代风格，自然景观",
        "现场（局部）参考局部": "局部景观，参考对比，细节展示",
        "线稿出图": "景观线稿，简约风格，自然线条",
        "白模（透视）": "景观白模，透视效果，自然景观",
        "白模（鸟瞰）": "景观鸟瞰，白模，高空视角",
        "白天转夜景": "夜景，灯光渲染，景观夜景",
        "亮化工程": "景观亮化，灯光设计，夜景照明",
        # 图像处理
        "指定换材质": "替换为新材质，材质转换",
        "修改局部": "局部修改，细节增强，精确编辑",
        "AI去除万物": "去除指定物体，智能清理",
        "AI去水印": "去除水印，智能修复",
        "增加物体": "添加新物体，智能合成",
        "增加物体（指定物体）": "添加指定物体，精确合成",
        "替换（产品）": "产品替换，智能替换",
        "替换（背景天花）": "替换背景或天花板，环境替换",
        "扩图": "扩展画面，智能扩展",
        "洗图": "图像清洗，去噪，质量提升",
        "图像增强": "图像增强，细节提升，清晰度优化",
        "溶图（局部）": "局部溶图，融合效果，自然过渡",
        "放大出图": "图像放大，高清，分辨率提升",
        "老照片修复": "老照片修复，去划痕，历史照片修复"
    }
    ADVANCED_DEFAULTS = {
        "室内设计-彩平图": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-毛坯房出图": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-线稿出图": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-白模渲染": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-多风格（白模）": {"控制强度": 0.58, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-多风格（线稿）": {"控制强度": 0.58, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-风格转换": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "室内设计-360出图": {"控制强度": 0.55, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-彩平图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-现场出图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-线稿出图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-白模透视（精确）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-白模透视（体块）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-白模鸟瞰（精确）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-白模鸟瞰（体块）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-白天变夜景": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "建筑规划-亮化工程": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-彩平图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-现场出图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-现场（局部）参考局部": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-线稿出图": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-白模（透视）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-白模（鸟瞰）": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-白天转夜景": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "景观设计-亮化工程": {"控制强度": 0.8, "参考图权重": 0.6, "参考图权重2": 0.6, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-指定换材质": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-修改局部": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-AI去除万物": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-AI去水印": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-增加物体": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-增加物体（指定物体）": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-替换（产品）": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-替换（背景天花）": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-扩图": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-洗图": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-图像增强": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-溶图（局部）": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-放大出图": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0},
        "图像处理-老照片修复": {"控制强度": 0.5, "参考图权重": 0.8, "参考图权重2": 0.8, "控制开始时间": 0, "控制结束时间": 1, "像素值": 0, "是否竖屏": False, "增强细节": 0}
    }
    def __init__(self, tabName, parent=None):
        super(TabContentWidget, self).__init__(parent)
        try:
            # 下拉栏选项映射（每个Tab不同）
            tab_options = {
                '室内设计': ['彩平图', '毛坯房出图', '线稿出图', '白模渲染', '多风格（白模）', '多风格（线稿）', '风格转换', '360出图'],
                '建筑规划': ['彩平图', '现场出图', '线稿出图', '白模透视（精确）', '白模透视（体块）', '白模鸟瞰（精确）', '白模鸟瞰（体块）', '白天变夜景', '亮化工程'],
                '景观设计': ['彩平图', '现场出图', '现场（局部）参考局部', '线稿出图', '白模（透视）', '白模（鸟瞰）', '白天转夜景', '亮化工程'],
                '图像处理': ['指定换材质', '修改局部', 'AI去除万物', 'AI去水印', '增加物体', '增加物体（指定物体）', '替换（产品）', '替换（背景天花）', '扩图', '洗图', '图像增强', '溶图（局部）', '放大出图', '老照片修复']
            }
            # 真正的内容widget
            contentWidget = QtWidgets.QWidget()
            contentWidget.setMaximumWidth(520)  # 统一内容区宽度
            contentLayout = QtWidgets.QVBoxLayout(contentWidget)
            contentLayout.setContentsMargins(0, 0, 0, 0)
            contentLayout.setSpacing(18)
        except Exception as e:
            import traceback
            error_msg = f"初始化TabContentWidget时出错: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            # 显示一个简单的错误消息
            errorLabel = QtWidgets.QLabel(f"初始化失败: {str(e)}")
            errorLabel.setStyleSheet("color: red; font-size: 16px;")
            errorLayout = QtWidgets.QVBoxLayout(self)
            errorLayout.addWidget(errorLabel)
            return
        # 下拉栏（悬浮）
        # 顶部标题
        self.titleLabel = QtWidgets.QLabel()
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.titleLabel.setText(tabName)  # 设置Tab名称作为标题
        # 主标题美化
        self.titleLabel.setStyleSheet("""
color: #fff;
font-size: 24px;
font-weight: bold;
letter-spacing: 2px;
text-align: center;
text-shadow: 1px 1px 4px #000;
""")
        
        # 保存Tab名称作为实例变量，用于API调用
        self.tabName = tabName
        # 初始化uploadWidget属性
        self.uploadWidget = None
        comboLabel = QtWidgets.QLabel(f"{tabName}选项：")
        # 分组标题美化
        comboLabel.setStyleSheet("color: #3af; font-size: 16px; font-weight: bold;")
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setFixedHeight(28)
        self.comboBox.setFixedWidth(180)
        self.comboBox.setStyleSheet("background-color: #444; color: white;")
        for opt in tab_options.get(tabName, []):
            self.comboBox.addItem(opt)
        comboBar = QtWidgets.QWidget()
        comboBarLayout = QtWidgets.QHBoxLayout(comboBar)
        comboBarLayout.setContentsMargins(0, 0, 0, 0)
        comboBarLayout.setSpacing(0)
        comboBarLayout.addStretch(1)
        comboBarLayout.addWidget(comboLabel)
        comboBarLayout.addSpacing(12)
        comboBarLayout.addWidget(self.comboBox)
        comboBarLayout.addStretch(1)
        # 动态内容区
        self.dynamicContent = QtWidgets.QWidget()
        self.dynamicLayout = QtWidgets.QVBoxLayout(self.dynamicContent)
        self.dynamicLayout.setContentsMargins(0, 0, 0, 0)
        self.dynamicLayout.setSpacing(18)
        contentLayout.addWidget(self.dynamicContent)
        # 外层用QScrollArea包裹
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidget(contentWidget)
        # 主布局：comboBar（顶部悬浮）+内容滚动区+生成按钮+获取视角按钮和显示区+底部按钮区
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(self.titleLabel)
        mainLayout.addWidget(comboBar)
        mainLayout.addWidget(scroll)
        # 生成按钮区（预留，后续动态添加）
        self.generateBtnContainer = QtWidgets.QWidget()
        self.generateBtnLayout = QtWidgets.QHBoxLayout(self.generateBtnContainer)
        self.generateBtnLayout.setContentsMargins(0, 18, 0, 0)
        self.generateBtnLayout.setSpacing(0)
        mainLayout.addWidget(self.generateBtnContainer)
        # 获取主视角按钮（隐藏显示区）
        self.captureBtn = QtWidgets.QPushButton("📷 获取主视角视图")
        self.captureBtn.setMinimumHeight(32)
        self.captureBtn.setMaximumHeight(36)
        self.captureBtn.setStyleSheet("""
QPushButton {
    background-color: #3da9fc;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
    padding: 4px 0;
}
QPushButton:hover {
    background-color: #2176c1;
}
QPushButton:pressed {
    background-color: #174e85;
}
""")
        self.captureBtn.setText("📷 获取主视角视图")
        # 创建隐藏的主视角图片组件（用于内部处理，不显示在界面上）
        self.viewImageWidget = ClickableImageView()
        self.viewImageWidget.hide()  # 隐藏主视角显示区域
        self.captureBtn.clicked.connect(self.capture_max_view)
        self.captureBtn.setEnabled(True)
        mainLayout.addWidget(self.captureBtn)
        # 不添加到主布局中，保持隐藏状态
        # 预留底部按钮区
        self.bottomBtnContainer = QtWidgets.QWidget()
        self.bottomBtnLayout = QtWidgets.QHBoxLayout(self.bottomBtnContainer)
        self.bottomBtnLayout.setContentsMargins(0, 18, 0, 0)
        self.bottomBtnLayout.setSpacing(0)
        mainLayout.addWidget(self.bottomBtnContainer)
        self.setLayout(mainLayout)
        # 绑定下拉栏切换事件和初始化，必须放在bottomBtnLayout创建之后
        self.comboBox.currentTextChanged.connect(self.updateDynamicUI)
        self.updateDynamicUI(self.comboBox.currentText())

    # 清空动态内容区
    def clearDynamicContent(self):
        clearLayout(self.dynamicLayout)
        # 清空底部按钮区
        clearLayout(self.bottomBtnLayout)

    # 样式常量
    PROMPT_EDIT_STYLE = """
        QLineEdit {
            background: #292929;
            color: #fff;
            border: 2px solid #3af;
            border-radius: 8px;
            font-size: 15px;
            padding: 6px 12px;
        }
        QLineEdit:focus {
            border: 2px solid #4bf;
            background: #222;
        }
    """
    PROMPT_EDIT_WIDTH = 260

    class UploadWithPromptWidget(QtWidgets.QWidget):
        def __init__(self, upload_label, prompt_label, prompt_default, parent=None):
            super().__init__(parent)
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            # 上传区居中
            upload = ImageUploadWidget(self)
            # 保存上传组件引用到父组件
            if hasattr(parent, 'uploadWidget'):
                parent.uploadWidget = upload
                print(f"🔧 设置uploadWidget: {upload}")
            else:
                print(f"❌ 父组件没有uploadWidget属性: {parent}")
            uploadRow = QtWidgets.QHBoxLayout()
            uploadRow.addStretch(1)
            uploadRow.addWidget(upload)
            uploadRow.addStretch(1)
            layout.addLayout(uploadRow)
            # 只在prompt_label有内容时才显示提示词输入框
            if prompt_label:
                vbox = QtWidgets.QVBoxLayout()
                vbox.setSpacing(6)
                label = QtWidgets.QLabel(prompt_label)
                label.setStyleSheet("color: #ccc; font-size: 14px;")
                label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                promptEdit = QtWidgets.QLineEdit()
                promptEdit.setFixedWidth(TabContentWidget.PROMPT_EDIT_WIDTH)
                promptEdit.setText(prompt_default)
                promptEdit.setStyleSheet(TabContentWidget.PROMPT_EDIT_STYLE)
                vbox.addWidget(label)
                vbox.addWidget(promptEdit)
                hbox = QtWidgets.QHBoxLayout()
                hbox.addStretch(1)
                hbox.addLayout(vbox)
                hbox.addStretch(1)
                layout.addLayout(hbox)

    # 配置驱动（选项名→上传区+提示词组）
    UPLOAD_PROMPT_CONFIG = {
        "多风格（白模）": [
            ("参考图像1", "提示词1", "书房，现代风格，书桌"),
            ("参考图像2", "提示词2", "卧室，现代风格"),
            ("参考图像3", "提示词3", "客厅，现代风格")
        ],
        "多风格（线稿)": [
            ("参考图像1", "提示词1", "卧室，现代风格"),
            ("参考图像2", "提示词2", "客厅，现代风格"),
            ("参考图像3", "提示词3", "书房，现代风格")
        ],
        # 其它多上传区选项可继续补充
    }
    
    # 参数需求配置（选项名→需要的参数列表）
    PARAM_REQUIREMENTS = {
        # 室内设计 - 基础选项，只需要基本参数
        "彩平图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "毛坯房出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "线稿出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "白模渲染": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "风格转换": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "360出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        
        # 多风格选项，需要多个提示词
        "多风格（白模）": ["workName", "workNameOne", "workNameTwo", "workStrong", "workStrongOne", "workWeight", "workWeightOne", "workStart", "workEnd"],
        "多风格（线稿）": ["workName", "workNameOne", "workNameTwo", "workStrong", "workStrongOne", "workWeight", "workWeightOne", "workStart", "workEnd"],
        
        # 建筑规划 - 基础选项
        "建筑规划-彩平图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-现场出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-线稿出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-白模透视（精确）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-白模透视（体块）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-白模鸟瞰（精确）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-白模鸟瞰（体块）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-白天变夜景": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "建筑规划-亮化工程": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        
        # 景观设计 - 基础选项
        "景观设计-彩平图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-现场出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-现场（局部）参考局部": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-线稿出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-白模（透视）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-白模（鸟瞰）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-白天转夜景": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "景观设计-亮化工程": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        
        # 图像处理 - 特殊选项，需要额外参数
        "图像处理-溶图（局部）": ["workName", "workStrong", "workWeight", "workWeightOne", "workStart", "workEnd", "workPixel", "workIsVertical"],
        "图像处理-放大出图": ["workName", "workStrong", "workWeight", "workStart", "workEnd", "workEnhance"],
        "图像处理-图像增强": ["workName", "workStrong", "workWeight", "workStart", "workEnd", "workEnhance"],
        
        # 图像处理 - 基础选项
        "图像处理-指定换材质": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-修改局部": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-AI去除万物": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-AI去水印": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-增加物体": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-增加物体（指定物体）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-替换（产品）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-替换（背景天花）": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-扩图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-洗图": ["workName", "workStrong", "workWeight", "workStart", "workEnd"],
        "图像处理-老照片修复": ["workName", "workStrong", "workWeight", "workStart", "workEnd"]
    }

    # updateDynamicUI重构
    def updateDynamicUI(self, option):
        self.clearDynamicContent()
        tabWidget = self.parent()
        tabName = ""
        if tabWidget and hasattr(tabWidget, 'parent') and tabWidget.parent() and hasattr(tabWidget.parent(), 'tabWidget'):
            idx = tabWidget.parent().tabWidget.currentIndex()
            tabName = tabWidget.parent().tabWidget.tabText(idx)
        optionText = self.comboBox.currentText()
        self.titleLabel.setText(optionText)
        # 针对"溶图（局部）"特殊处理：2上传区+1提示词
        if option == "溶图（局部）":
            upload_labels = ["参考图像1", "参考图像2"]
            for label in upload_labels:
                # 只显示上传区，不显示提示词输入框
                widget = self.UploadWithPromptWidget(label, None, None)
                self.dynamicLayout.addWidget(widget)
                self.dynamicLayout.addSpacing(12)
            # 只加一个提示词输入框
            vbox = QtWidgets.QVBoxLayout()
            vbox.setSpacing(6)
            label = QtWidgets.QLabel("提示词")
            label.setStyleSheet("color: #ccc; font-size: 14px;")
            label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            promptEdit = QtWidgets.QLineEdit()
            promptEdit.setFixedWidth(TabContentWidget.PROMPT_EDIT_WIDTH)
            promptEdit.setText(self.PROMPT_DEFAULTS.get(option, ""))
            promptEdit.setStyleSheet(TabContentWidget.PROMPT_EDIT_STYLE)
            vbox.addWidget(label)
            vbox.addWidget(promptEdit)
            hbox = QtWidgets.QHBoxLayout()
            hbox.addStretch(1)
            hbox.addLayout(vbox)
            hbox.addStretch(1)
            self.dynamicLayout.addLayout(hbox)
            # 添加高级参数区（滑块风格）
            advGroup = CollapsibleWidget("高级参数设置")
            advLayout = QtWidgets.QVBoxLayout()
            advLayout.setContentsMargins(8, 0, 8, 4)
            advLayout.setSpacing(6)
            slider_style = """
                QSlider::groove:horizontal {
                    border: 1px solid #222;
                    height: 8px;
                    background: #444;
                    border-radius: 4px;
                }
                QSlider::sub-page:horizontal {
                    background: #3af;
                    border-radius: 4px;
                }
                QSlider::add-page:horizontal {
                    background: #222;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #fff;
                    border: 2px solid #3af;
                    width: 18px;
                    height: 18px;
                    margin: -5px 0;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal:hover {
                    background: #4bf;
                    border: 2px solid #fff;
                }
            """
            for idx in [1, 2]:
                paramLayout = QtWidgets.QHBoxLayout()
                paramLayout.setContentsMargins(16, 0, 0, 0)
                paramLayout.setSpacing(10)
                paramLabel = QtWidgets.QLabel(f"参考图{idx}权重")
                paramLabel.setStyleSheet("color: white; font-size: 13px; min-width: 80px;")
                paramSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                paramSlider.setMinimum(0)
                paramSlider.setMaximum(100)
                paramSlider.setValue(60 if idx == 1 else 70)
                paramSlider.setFixedWidth(120)
                paramSlider.setStyleSheet(slider_style)
                paramValue = QtWidgets.QLineEdit(str((60 if idx == 1 else 70)/100.0))
                paramValue.setFixedWidth(40)
                paramValue.setAlignment(QtCore.Qt.AlignCenter)
                paramValue.setStyleSheet("background-color: #333; color: white; border: 1px solid #555; font-size: 14px;")
                def createSliderCallback(slider, valueEdit):
                    def sliderChanged(val):
                        valueEdit.setText(f"{val/100.0:.2f}")
                    return sliderChanged
                def createValueCallback(slider, valueEdit):
                    def valueChanged():
                        try:
                            v = float(valueEdit.text())
                            v = max(0.0, min(1.0, v))
                            slider.setValue(int(v*100))
                        except:
                            pass
                    return valueChanged
                paramSlider.valueChanged.connect(createSliderCallback(paramSlider, paramValue))
                paramValue.editingFinished.connect(createValueCallback(paramSlider, paramValue))
                container = QtWidgets.QWidget()
                containerLayout = QtWidgets.QHBoxLayout(container)
                containerLayout.setContentsMargins(0, 0, 0, 0)
                containerLayout.setSpacing(10)
                containerLayout.addWidget(paramLabel)
                containerLayout.addWidget(paramSlider)
                containerLayout.addWidget(paramValue)
                container.setFixedWidth(260)
                paramLayout.addWidget(container)
                advLayout.addLayout(paramLayout)
            advGroup.setContentLayout(advLayout)
            self.dynamicLayout.addWidget(advGroup)
            return
        # 配置驱动多上传区+多提示词
        if option in self.UPLOAD_PROMPT_CONFIG or option in ["多风格（白模）", "多风格（线稿）"]:
            config = self.UPLOAD_PROMPT_CONFIG.get(option)
            if config:
                for i, (upload_label, prompt_label, prompt_default) in enumerate(config):
                    widget = self.UploadWithPromptWidget(upload_label, prompt_label, prompt_default, self)
                    self.dynamicLayout.addWidget(widget)
                    if i < len(config) - 1:
                        self.dynamicLayout.addSpacing(12)
            else:
                # 默认3组上传区+提示词
                for i in range(3):
                        upload_label = f"参考图像{i+1}"
                        prompt_label = f"提示词{i+1}"
                        prompt_default = self.MULTI_PROMPT_DEFAULTS.get(option, ["", "", ""])[i]
                        widget = self.UploadWithPromptWidget(upload_label, prompt_label, prompt_default, self)
                        self.dynamicLayout.addWidget(widget)
                if i < 2:
                    self.dynamicLayout.addSpacing(12)
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
        else:
            # 单上传区+单提示词
            widget = self.UploadWithPromptWidget("参考图像", "提示词", self.PROMPT_DEFAULTS.get(option, ""), self)
            self.dynamicLayout.addWidget(widget)
            if tabName == "图像处理" or option in ["彩平图", "线稿出图", "风格转换"]:
                self.dynamicLayout.addLayout(self._strengthSlider())
                self.dynamicLayout.addWidget(self._advancedParams())
        self._addBottomBtn(self._generateBtn())

    # 复用控件生成函数
    def _uploadGroup(self, multi=False, label_text="参考图像"):
        group = QtWidgets.QGroupBox(label_text if not multi else "")
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 15px;
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                padding-top: 0px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 10px;
                top: 2px;
                padding: 0 3px;
            }
        """)
        group.setFixedHeight(320)
        group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        if not multi:
            uploadContainer = QtWidgets.QWidget()
            uploadContainer.setFixedSize(260, 240)
            uploadContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            # 只保留上传控件，不再有QTabWidget
            uploadWidget = ImageUploadWidget(uploadContainer)
            uploadWidget.move(0, 0)
            # 保存上传组件引用
            self.uploadWidget = uploadWidget
            uploadRow = QtWidgets.QHBoxLayout()
            uploadRow.setContentsMargins(0, 0, 0, 0)
            uploadRow.setSpacing(0)
            uploadRow.addStretch(1)
            uploadRow.addWidget(uploadContainer)
            uploadRow.addStretch(1)
            layout.addLayout(uploadRow)
        else:
            for i in range(2):
                groupWidget = QtWidgets.QWidget()
                vbox = QtWidgets.QVBoxLayout(groupWidget)
                vbox.setContentsMargins(0, 0, 0, 0)
                vbox.setSpacing(6)
                label = QtWidgets.QLabel(f"参考图像{i+1}")
                label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                label.setStyleSheet("color: #fff; font-size: 13px; font-weight: bold; margin-bottom: 2px;")
                labelRow = QtWidgets.QHBoxLayout()
                labelRow.setContentsMargins(0, 0, 0, 0)
                labelRow.setSpacing(0)
                labelRow.addSpacing(16)
                labelRow.addWidget(label)
                labelRow.addStretch(1)
                vbox.addLayout(labelRow)
                uploadContainer = QtWidgets.QWidget()
                uploadContainer.setFixedSize(260, 240)
                uploadContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                # 只保留上传控件，不再有QTabWidget
                uploadWidget = ImageUploadWidget(uploadContainer, custom_height=240)
                uploadWidget.move(0, 0)
                vbox.addWidget(uploadContainer)
                uploadRow = QtWidgets.QHBoxLayout()
                uploadRow.setContentsMargins(0, 0, 0, 0)
                uploadRow.setSpacing(0)
                uploadRow.addStretch(1)
                uploadRow.addWidget(groupWidget)
                uploadRow.addStretch(1)
                layout.addLayout(uploadRow)
                if i < 1:
                    layout.addSpacing(12)
        return group

    def _promptInput(self, prompt_index=0, option=None):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)  # label和输入框间距更小
        if option in self.MULTI_PROMPT_DEFAULTS:
            defaults = self.MULTI_PROMPT_DEFAULTS[option]
            default = defaults[prompt_index] if prompt_index < len(defaults) else ""
            label = QtWidgets.QLabel(f"提示词{prompt_index+1}" if len(defaults) > 1 else "提示词")
        else:
            optionText = option if option else (self.comboBox.currentText() if hasattr(self, "comboBox") else "")
            default = self.PROMPT_DEFAULTS.get(optionText, "")
            label = QtWidgets.QLabel("提示词")
        label.setStyleSheet("color: #ccc; font-size: 14px; margin-bottom: 0px;")
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        promptEdit = QtWidgets.QLineEdit()
        promptEdit.setFixedWidth(TabContentWidget.PROMPT_EDIT_WIDTH)
        promptEdit.setText(default)
        promptEdit.setStyleSheet("""
            QLineEdit {
                background: #292929;
                color: #fff;
                border: 2px solid #3af;
                border-radius: 8px;
                font-size: 15px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4bf;
                background: #222;
            }
        """)
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)
        vbox.addWidget(label)
        vbox.addWidget(promptEdit)
        layout.addLayout(vbox)
        return layout

    def _strengthSlider(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(16, 0, 0, 0)  # 左边与上传区对齐
        layout.setSpacing(10)
        strengthLabel = QtWidgets.QLabel("控制强度")
        # 普通标签美化
        strengthLabel.setStyleSheet("color: #ccc; font-size: 14px;")
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(55)
        slider.setFixedWidth(140)
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #222;
                height: 8px;
                background: #444;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #3af;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #222;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 2px solid #3af;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #4bf;
                border: 2px solid #fff;
            }
        """
        slider.setStyleSheet(slider_style)
        valueEdit = QtWidgets.QLineEdit("0.55")
        valueEdit.setFixedWidth(50)
        valueEdit.setAlignment(QtCore.Qt.AlignCenter)
        # 输入框美化
        valueEdit.setStyleSheet("background-color: #222; color: white; border: 1px solid #3af; font-size: 14px;")
        def sliderChanged(val):
            valueEdit.setText(f"{val/100.0:.2f}")
        slider.valueChanged.connect(sliderChanged)
        def valueEditChanged():
            try:
                v = float(valueEdit.text())
                v = max(0.0, min(1.0, v))
                slider.setValue(int(v*100))
            except:
                pass
        valueEdit.editingFinished.connect(valueEditChanged)
        container = QtWidgets.QWidget()
        containerLayout = QtWidgets.QHBoxLayout(container)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(10)
        containerLayout.addWidget(strengthLabel)
        containerLayout.addWidget(slider)
        containerLayout.addWidget(valueEdit)
        container.setFixedWidth(260)  # 与上传区宽度一致
        layout.addWidget(container)
        # layout.addStretch(1)  # 不再右侧拉伸
        return layout

    def _advancedParams(self):
        collapse = CollapsibleWidget("高级参数设置")
        advancedLayout = QtWidgets.QVBoxLayout()
        advancedLayout.setContentsMargins(8, 0, 8, 4)  # 标题和内容区更贴合
        advancedLayout.setSpacing(6)
        advancedParams = [
            ("参考图权重", 0, 100, 80),
            ("控制开始时间", 0, 100, 0),
            ("控制结束时间", 0, 100, 100)
        ]
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #222;
                height: 8px;
                background: #444;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #3af;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #222;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 2px solid #3af;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #4bf;
                border: 2px solid #fff;
            }
        """
        for paramName, minVal, maxVal, defaultVal in advancedParams:
            paramLayout = QtWidgets.QHBoxLayout()
            paramLayout.setContentsMargins(16, 0, 0, 0)  # 左对齐上传区
            paramLayout.setSpacing(10)
            paramLabel = QtWidgets.QLabel(paramName)
            paramLabel.setStyleSheet("color: white; font-size: 13px; min-width: 80px;")
            paramSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            paramSlider.setMinimum(minVal)
            paramSlider.setMaximum(maxVal)
            paramSlider.setValue(defaultVal)
            paramSlider.setFixedWidth(120)
            paramSlider.setStyleSheet(slider_style)
            paramValue = QtWidgets.QLineEdit(str(defaultVal/100.0))
            paramValue.setFixedWidth(40)
            paramValue.setAlignment(QtCore.Qt.AlignCenter)
            # 输入框美化
            paramValue.setStyleSheet("background-color: #333; color: white; border: 1px solid #555; font-size: 14px;")
            def createSliderCallback(slider, valueEdit):
                def sliderChanged(val):
                    valueEdit.setText(f"{val/100.0:.2f}")
                return sliderChanged
            def createValueCallback(slider, valueEdit):
                def valueChanged():
                    try:
                        v = float(valueEdit.text())
                        v = max(0.0, min(1.0, v))
                        slider.setValue(int(v*100))
                    except:
                        pass
                return valueChanged
            paramSlider.valueChanged.connect(createSliderCallback(paramSlider, paramValue))
            paramValue.editingFinished.connect(createValueCallback(paramSlider, paramValue))
            container = QtWidgets.QWidget()
            containerLayout = QtWidgets.QHBoxLayout(container)
            containerLayout.setContentsMargins(0, 0, 0, 0)
            containerLayout.setSpacing(10)
            containerLayout.addWidget(paramLabel)
            containerLayout.addWidget(paramSlider)
            containerLayout.addWidget(paramValue)
            container.setFixedWidth(260)  # 与上传区宽度一致
            paramLayout.addWidget(container)
            # paramLayout.addStretch(1)  # 不再右侧拉伸
            advancedLayout.addLayout(paramLayout)
        collapse.setContentLayout(advancedLayout)
        return collapse

    def _generateBtn(self):
        btn = QtWidgets.QPushButton("立即生成 ✨")
        btn.setMinimumWidth(240)  # 加宽
        btn.setFixedHeight(48)    # 更高
        btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        # 主操作按钮美化
        btn.setStyleSheet("""
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4bf, stop:1 #3af);
    color: white;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 2px;
    border: none;
    border-radius: 12px;
    padding: 8px 0;
}
QPushButton:hover {
    background: #5cf;
}
QPushButton:pressed {
    background: #2af;
}
""")
        btn.clicked.connect(self.onGenerateClicked)
        return btn

    def onGenerateClicked(self):
        # 获取当前Tab和下拉选项
        tabName = ""
        tabWidget = None  # 初始化tabWidget变量
        print(f"🔍 调试Tab名称获取:")
        
        # 方法1：使用保存的Tab名称
        if hasattr(self, 'tabName'):
            tabName = self.tabName
            print(f"  ✅ 通过保存的tabName获取Tab名称: {tabName}")
        else:
            # 方法2：通过TabContentWidget的titleLabel获取Tab名称
            if hasattr(self, 'titleLabel') and self.titleLabel.text():
                tabName = self.titleLabel.text()
                print(f"  ✅ 通过titleLabel获取Tab名称: {tabName}")
            else:
                # 方法3：通过父级结构获取Tab名称
                tabWidget = self.parent()
                print(f"  tabWidget: {tabWidget}")
                print(f"  tabWidget.parent(): {tabWidget.parent() if tabWidget else None}")
                
        if tabWidget and hasattr(tabWidget, 'parent') and tabWidget.parent() and hasattr(tabWidget.parent(), 'tabWidget'):
            idx = tabWidget.parent().tabWidget.currentIndex()
            tabName = tabWidget.parent().tabWidget.tabText(idx)
            print(f"  tabWidget.parent().tabWidget: {tabWidget.parent().tabWidget}")
            print(f"  currentIndex: {idx}")
            print(f"  tabText: {tabName}")
        else:
            print(f"  ❌ 无法获取Tab信息")
            
        option = self.comboBox.currentText()
        print(f"  option: {option}")
        print(f"  tabName: '{tabName}'")
        
        # 分流到不同的API调用函数
        if tabName == "室内设计":
            print(f"✅ 调用室内设计API: {option}")
            self.call_api_interior(option)
        elif tabName == "建筑规划":
            print(f"✅ 调用建筑规划API: {option}")
            self.call_api_architecture(option)
        elif tabName == "景观设计":
            print(f"✅ 调用景观设计API: {option}")
            self.call_api_landscape(option)
        elif tabName == "图像处理":
            print(f"✅ 调用图像处理API: {option}")
            self.call_api_image(option)
        else:
            print(f"❌ 未匹配的Tab: '{tabName}'，调用默认API: {option}")
            self.call_api_default(option)

    # 下面是预留的API调用函数，后续直接填参数和实现即可
    def call_api_interior(self, option):
        if option == "彩平图":
            self.api_interior_cai_ping_tu()
        elif option == "毛坯房出图":
            self.api_interior_mao_pi_fang()
        elif option == "线稿出图":
            self.api_interior_xian_gao()
        elif option == "白模渲染":
            self.api_interior_bai_mo()
        elif option == "多风格（白模）":
            self.api_interior_duo_fengge_baimo()
        elif option == "多风格（线稿）":
            self.api_interior_duo_fengge_xiangao()
        elif option == "风格转换":
            self.api_interior_fengge_zhuanhuan()
        elif option == "360出图":
            self.api_interior_360()
        elif option == "室内-多角度(白模)":
            self.api_interior_duo_fengge_baimo()
        elif option == "室内-多角度(线稿)":
            self.api_interior_duo_fengge_xiangao()
        else:
            print(f"未实现的室内设计API: {option}")

    def api_interior_cai_ping_tu(self):
        """室内设计-彩平图API"""
        return self.call_workflow_api("彩平图", "室内设计")
        
    def api_interior_mao_pi_fang(self):
        """室内设计-毛坯房出图API"""
        return self.call_workflow_api("毛坯房出图", "室内设计")
        
    def api_interior_xian_gao(self):
        """室内设计-线稿出图API"""
        return self.call_workflow_api("线稿出图", "室内设计")
        
    def api_interior_bai_mo(self):
        """室内设计-白模渲染API"""
        return self.call_workflow_api("白模渲染", "室内设计")
        
    def api_interior_duo_fengge_baimo(self):
        """室内设计-多风格（白模）API"""
        return self.call_workflow_api("多风格（白模）", "室内设计")
        
    def api_interior_duo_fengge_xiangao(self):
        """室内设计-多风格（线稿）API"""
        return self.call_workflow_api("多风格（线稿）", "室内设计")
        
    def api_interior_fengge_zhuanhuan(self):
        """室内设计-风格转换API"""
        return self.call_workflow_api("风格转换", "室内设计")
        
    def api_interior_360(self):
        """室内设计-360出图API"""
        return self.call_workflow_api("360出图", "室内设计")

    def call_api_architecture(self, option):
        if option == "彩平图":
            self.api_arch_cai_ping_tu()
        elif option == "现场出图":
            self.api_arch_xian_chang()
        elif option == "线稿出图":
            self.api_arch_xian_gao()
        elif option == "白模透视（精确）":
            self.api_arch_baimo_toushi_jingque()
        elif option == "白模透视（体块）":
            self.api_arch_baimo_toushi_tikuai()
        elif option == "白模鸟瞰（精确）":
            self.api_arch_baimo_niokan_jingque()
        elif option == "白模鸟瞰（体块）":
            self.api_arch_baimo_niokan_tikuai()
        elif option == "白天变夜景":
            self.api_arch_baitian_yejing()
        elif option == "亮化工程":
            self.api_arch_lianghua()
        else:
            print(f"未实现的建筑规划API: {option}")

    def api_arch_cai_ping_tu(self):
        """建筑规划-彩平图API"""
        return self.call_workflow_api("彩平图", "建筑规划")
        
    def api_arch_xian_chang(self):
        """建筑规划-现场出图API"""
        return self.call_workflow_api("现场出图", "建筑规划")
        
    def api_arch_xian_gao(self):
        """建筑规划-线稿出图API"""
        return self.call_workflow_api("线稿出图", "建筑规划")
        
    def api_arch_baimo_toushi_jingque(self):
        """建筑规划-白模透视（精确）API"""
        return self.call_workflow_api("白模透视（精确）", "建筑规划")
        
    def api_arch_baimo_toushi_tikuai(self):
        """建筑规划-白模透视（体块）API"""
        return self.call_workflow_api("白模透视（体块）", "建筑规划")
        
    def api_arch_baimo_niokan_jingque(self):
        """建筑规划-白模鸟瞰（精确）API"""
        return self.call_workflow_api("白模鸟瞰（精确）", "建筑规划")
        
    def api_arch_baimo_niokan_tikuai(self):
        """建筑规划-白模鸟瞰（体块）API"""
        return self.call_workflow_api("白模鸟瞰（体块）", "建筑规划")
        
    def api_arch_baitian_yejing(self):
        """建筑规划-白天变夜景API"""
        return self.call_workflow_api("白天变夜景", "建筑规划")
        
    def api_arch_lianghua(self):
        """建筑规划-亮化工程API"""
        return self.call_workflow_api("亮化工程", "建筑规划")

    def call_api_landscape(self, option):
        if option == "彩平图":
            self.api_land_cai_ping_tu()
        elif option == "现场出图":
            self.api_land_xian_chang()
        elif option == "现场（局部）参考局部":
            self.api_land_xian_chang_jubu()
        elif option == "线稿出图":
            self.api_land_xian_gao()
        elif option == "白模（透视）":
            self.api_land_baimo_toushi()
        elif option == "白模（鸟瞰）":
            self.api_land_baimo_niokan()
        elif option == "白天转夜景":
            self.api_land_baitian_yejing()
        elif option == "亮化工程":
            self.api_land_lianghua()
        else:
            print(f"未实现的景观设计API: {option}")

    def api_land_cai_ping_tu(self):
        """景观设计-彩平图API"""
        return self.call_workflow_api("彩平图", "景观设计")
        
    def api_land_xian_chang(self):
        """景观设计-现场出图API"""
        return self.call_workflow_api("现场出图", "景观设计")
        
    def api_land_xian_chang_jubu(self):
        """景观设计-现场（局部）参考局部API"""
        return self.call_workflow_api("现场（局部）参考局部", "景观设计")
        
    def api_land_xian_gao(self):
        """景观设计-线稿出图API"""
        return self.call_workflow_api("线稿出图", "景观设计")
        
    def api_land_baimo_toushi(self):
        """景观设计-白模（透视）API"""
        return self.call_workflow_api("白模（透视）", "景观设计")
        
    def api_land_baimo_niokan(self):
        """景观设计-白模（鸟瞰）API"""
        return self.call_workflow_api("白模（鸟瞰）", "景观设计")
        
    def api_land_baitian_yejing(self):
        """景观设计-白天转夜景API"""
        return self.call_workflow_api("白天转夜景", "景观设计")
        
    def api_land_lianghua(self):
        """景观设计-亮化工程API"""
        return self.call_workflow_api("亮化工程", "景观设计")

    def call_api_image(self, option):
        if option == "指定换材质":
            self.api_img_huancai()
        elif option == "修改局部":
            self.api_img_xiugai_jubu()
        elif option == "AI去除万物":
            self.api_img_quchu()
        elif option == "AI去水印":
            self.api_img_shuiyin()
        elif option == "增加物体":
            self.api_img_zengjia()
        elif option == "增加物体（指定物体）":
            self.api_img_zengjia_zhiding()
        elif option == "替换（产品）":
            self.api_img_tihuan_chanpin()
        elif option == "替换（背景天花）":
            self.api_img_tihuan_beijing()
        elif option == "扩图":
            self.api_img_kuotu()
        elif option == "洗图":
            self.api_img_xitu()
        elif option == "图像增强":
            self.api_img_enhance()
        elif option == "溶图（局部）":
            self.api_img_rongtu()
        elif option == "放大出图":
            self.api_img_fangda()
        elif option == "老照片修复":
            self.api_img_repair()
        else:
            print(f"未实现的图像处理API: {option}")

    def api_img_huancai(self):
        """图像处理-指定换材质API"""
        return self.call_workflow_api("指定换材质", "图像处理")
        
    def api_img_xiugai_jubu(self):
        """图像处理-修改局部API"""
        return self.call_workflow_api("修改局部", "图像处理")
        
    def api_img_quchu(self):
        """图像处理-AI去除万物API"""
        return self.call_workflow_api("AI去除万物", "图像处理")
        
    def api_img_shuiyin(self):
        """图像处理-AI去水印API"""
        return self.call_workflow_api("AI去水印", "图像处理")
        
    def api_img_zengjia(self):
        """图像处理-增加物体API"""
        return self.call_workflow_api("增加物体", "图像处理")
        
    def api_img_zengjia_zhiding(self):
        """图像处理-增加物体（指定物体）API"""
        return self.call_workflow_api("增加物体（指定物体）", "图像处理")
        
    def api_img_tihuan_chanpin(self):
        """图像处理-替换（产品）API"""
        return self.call_workflow_api("替换（产品）", "图像处理")
        
    def api_img_tihuan_beijing(self):
        """图像处理-替换（背景天花）API"""
        return self.call_workflow_api("替换（背景天花）", "图像处理")
        
    def api_img_kuotu(self):
        """图像处理-扩图API"""
        return self.call_workflow_api("扩图", "图像处理")
        
    def api_img_xitu(self):
        """图像处理-洗图API"""
        return self.call_workflow_api("洗图", "图像处理")
        
    def api_img_enhance(self):
        """图像处理-图像增强API"""
        return self.call_workflow_api("图像增强", "图像处理")
        
    def api_img_rongtu(self):
        """图像处理-溶图（局部）API"""
        return self.call_workflow_api("溶图（局部）", "图像处理")
        
    def api_img_fangda(self):
        """图像处理-放大出图API"""
        return self.call_workflow_api("放大出图", "图像处理")
        
    def api_img_repair(self):
        """图像处理-老照片修复API"""
        return self.call_workflow_api("老照片修复", "图像处理")

    def call_api_default(self, option):
        print(f"[API] 默认: {option}")
        # TODO: 其它情况的API调用
        pass

    # =========================
    # 核心API调用方法
    # =========================
    
    def call_workflow_api(self, option_name, tab_name):
        """调用工作流API"""
        try:
            print(f"调用API: {tab_name}-{option_name}")
            
            # 显示任务进度条
            main_panel = self.get_main_panel()
            if main_panel:
                main_panel.show_task_progress(True)
                main_panel.update_task_progress(0, "准备中...")
            
            # 0. 检查登录状态，如果没有token则强制登录
            print("🔐 检查登录状态...")
            login_data = get_auto_login_info()
            if not login_data or not login_data.get('token'):
                print("❌ 没有找到token，需要先登录")
                self.show_error_message("请先登录，获取token后才能调用API")
                if main_panel:
                    main_panel.show_task_progress(False)
                return None
            else:
                print(f"✅ 找到token: {login_data.get('token')[:20]}...")
            
            # 1. 在获取主视角视图之前先隐藏UI元素
            print("🎯 开始隐藏UI元素...")
            try:
                import pymxs
                rt = pymxs.runtime
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
                rt.execute(hide_ui_code)
                print("✅ UI元素隐藏成功")
            except Exception as e:
                print(f"⚠️ 隐藏UI元素失败: {str(e)}")
            
            # 2. 自动获取主视角视图作为原始图像
            print("📷 自动获取主视角视图...")
            if main_panel:
                main_panel.update_task_progress(10, "获取主视角视图...")
            
            original_image_path = self.capture_max_view()
            if not original_image_path:
                self.show_error_message("主视角视图获取失败")
                if main_panel:
                    main_panel.show_task_progress(False)
                return None
                
            # 2. 上传图像到服务器
            print("📤 上传主视角图像...")
            if main_panel:
                main_panel.update_task_progress(20, "上传主视角图像...")
            original_image_url = self.upload_image(original_image_path)
            if not original_image_url:
                print("❌ 主视角图像上传失败")
                self.show_error_message("主视角图像上传失败")
                if main_panel:
                    main_panel.show_task_progress(False)
                return None
            print(f"✅ 主视角图像上传成功: {original_image_url}")
                
            # 3. 获取用户上传的图像作为参考图像
            reference_image_url = None
            reference_image_path = self.get_uploaded_image_path()
            print(f"🔍 检查参考图像路径: {reference_image_path}")
            if reference_image_path and os.path.exists(reference_image_path):
                print("📤 上传参考图像...")
                if main_panel:
                    main_panel.update_task_progress(30, "上传参考图像...")
                reference_image_url = self.upload_image(reference_image_path)
                if reference_image_url:
                    print(f"✅ 参考图像上传成功: {reference_image_url}")
                else:
                    print("⚠️ 参考图像上传失败，继续处理")
            else:
                print("⚠️ 没有找到参考图像或文件不存在")
                if not reference_image_path:
                    print("❌ 参考图像路径为空")
                elif not os.path.exists(reference_image_path):
                    print(f"❌ 参考图像文件不存在: {reference_image_path}")
                
            # 4. 获取工作类型
            work_type_key = f"{tab_name}-{option_name}"
            work_type = WORK_TYPE_MAP.get(work_type_key, 100)
            print(f"🔍 工作类型映射: {work_type_key} -> {work_type}")
            
            # 5. 获取提示词（支持多提示词）
            multi_prompts = self.get_multi_prompts()
            prompt_text = multi_prompts[0] if multi_prompts else "默认提示词"
            prompt_one = multi_prompts[1] if len(multi_prompts) > 1 else ""
            prompt_two = multi_prompts[2] if len(multi_prompts) > 2 else ""
            
            print(f"📝 提示词配置:")
            print(f"  - 主要提示词: {prompt_text}")
            print(f"  - 提示词1: {prompt_one}")
            print(f"  - 提示词2: {prompt_two}")
            
            # 6. 获取高级参数
            strength_value = self.get_strength_value()
            weight_value = self.get_weight_value()
            weight_one_value = self.get_weight_one_value()
            start_value = self.get_start_value()
            end_value = self.get_end_value()
            pixel_value = self.get_pixel_value()
            is_vertical = self.get_is_vertical()
            enhance_value = self.get_enhance_value()
            
            # 7. 根据选项确定需要的参数
            work_type_key = f"{tab_name}-{option_name}"
            required_params = self.PARAM_REQUIREMENTS.get(option_name, [])
            if not required_params:
                # 如果没有找到具体选项，尝试使用Tab+选项的组合
                required_params = self.PARAM_REQUIREMENTS.get(work_type_key, ["workName", "workStrong", "workWeight", "workStart", "workEnd"])
            
            print(f"🎚️ 参数需求分析:")
            print(f"  - 选项: {option_name}")
            print(f"  - 工作类型键: {work_type_key}")
            print(f"  - 需要参数: {required_params}")
            
            # 8. 动态构建参数
            params = {
                "workOriginAvatar": original_image_url,      # 主视角视图作为原始图像（URL）
                "workType": work_type,
                "workReferenceAvatar": reference_image_url if reference_image_url else "",  # 参考图像（URL）
                "workExtendAvatar": "",                     # 扩展图像1 (暂时为空)
                "workExtendAvatarOne": "",                  # 扩展图像2 (暂时为空)
                "workId": "",                               # 工作ID (暂时为空)
                "workFlowId": "",                           # 工作流ID (暂时为空)
                "workMask": "",                             # 遮罩1 (必填，但可以为空)
                "workMaskOne": ""                           # 遮罩2 (必填，但可以为空)
            }
            
            # 根据需要的参数动态添加
            if "workName" in required_params:
                params["workName"] = prompt_text
            if "workNameOne" in required_params:
                params["workNameOne"] = prompt_one
            if "workNameTwo" in required_params:
                params["workNameTwo"] = prompt_two
            if "workStrong" in required_params:
                params["workStrong"] = strength_value
            if "workStrongOne" in required_params:
                params["workStrongOne"] = strength_value
            if "workWeight" in required_params:
                params["workWeight"] = weight_value
            if "workWeightOne" in required_params:
                params["workWeightOne"] = weight_one_value
            if "workStart" in required_params:
                params["workStart"] = start_value
            if "workEnd" in required_params:
                params["workEnd"] = end_value
            if "workPixel" in required_params:
                params["workPixel"] = pixel_value
            if "workIsVertical" in required_params:
                params["workIsVertical"] = is_vertical
            if "workEnhance" in required_params:
                params["workEnhance"] = enhance_value
            
            print(f"🎚️ 最终参数配置:")
            for key, value in params.items():
                if key in ["workOriginAvatar", "workReferenceAvatar", "workExtendAvatar", "workExtendAvatarOne", "workId", "workFlowId", "workMask", "workMaskOne"]:
                    continue  # 跳过固定参数
                print(f"  - {key}: {value}")
            
            print(f"🚀 发送立即生成请求:")
            print(f"📋 请求参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
            
            if main_panel:
                main_panel.update_task_progress(40, "发送API请求...")
            
            response = self.call_api_request(API_ENDPOINTS["workflow"], params)
            
            if response and response.get("code") == 0:
                print(f"✅ 立即生成请求成功:")
                print(f"📥 响应数据: {json.dumps(response, ensure_ascii=False, indent=2)}")
                
                # 获取任务ID - 从响应数据中提取正确的ID
                work_id = response.get("data", {}).get("workId")
                task_id = response.get("data", {}).get("resultTask", {}).get("data", {}).get("taskId")
                flow_id = response.get("data", {}).get("flowId")
                
                if work_id:
                    print(f"🆔 工作ID: {work_id}")
                    print(f"🔄 流程ID: {flow_id}")
                    print(f"📋 任务ID: {task_id}")
                    print(f"🎉 任务已提交，开始监控进度...")
                    if main_panel:
                        main_panel.update_task_progress(50, "任务已提交，开始监控...")
                    # 重新启用任务监控，使用正确的工作ID和流程ID
                    self.monitor_task_progress(work_id, flow_id)
                else:
                    print("⚠️ 未获取到任务ID，无法监控进度")
                    if main_panel:
                        main_panel.show_task_progress(False)
                
                self.show_success_message("任务已提交，正在处理中...")
                
                # 恢复UI元素
                print("🎯 开始恢复UI元素...")
                try:
                    import pymxs
                    rt = pymxs.runtime
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
                    rt.execute(restore_ui_code)
                    print("✅ UI元素恢复成功")
                except Exception as restore_e:
                    print(f"⚠️ 恢复UI元素失败: {str(restore_e)}")
                
                return response
            else:
                error_msg = response.get("msg", "未知错误") if response else "网络错误"
                print(f"❌ 立即生成请求失败: {error_msg}")
                self.show_error_message(f"API调用失败: {error_msg}")
                if main_panel:
                    main_panel.show_task_progress(False)
                
                # 恢复UI元素
                print("🎯 开始恢复UI元素...")
                try:
                    import pymxs
                    rt = pymxs.runtime
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
                    rt.execute(restore_ui_code)
                    print("✅ UI元素恢复成功")
                except Exception as restore_e:
                    print(f"⚠️ 恢复UI元素失败: {str(restore_e)}")
                
                return None
                
        except Exception as e:
            print(f"API调用异常: {str(e)}")
            self.show_error_message(f"API调用异常: {str(e)}")
            # 隐藏进度条
            main_panel = self.get_main_panel()
            if main_panel:
                main_panel.show_task_progress(False)
            
            # 恢复UI元素
            print("🎯 开始恢复UI元素...")
            try:
                import pymxs
                rt = pymxs.runtime
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
                rt.execute(restore_ui_code)
                print("✅ UI元素恢复成功")
            except Exception as restore_e:
                print(f"⚠️ 恢复UI元素失败: {str(restore_e)}")
            
            return None
    
    def monitor_task_progress(self, task_id, flow_id=None):
        """监控任务进度 - 优化版本，减少不必要的请求"""
        print(f"📊 开始监控任务进度: {task_id}")
        if flow_id:
            print(f"🔄 流程ID: {flow_id}")
        
        # 获取主界面引用并显示进度条
        main_panel = self.get_main_panel()
        if main_panel:
            main_panel.show_task_progress(True)
            main_panel.update_task_progress(0, "准备中...")
        
        # 使用QTimer进行异步监控，避免阻塞主线程
        self.monitor_timer = QtCore.QTimer()
        self.monitor_timer.timeout.connect(lambda: self._monitor_task_step(task_id, flow_id, main_panel))
        
        # 监控状态变量 - 优化配置
        self.monitor_attempt = 0
        self.monitor_max_attempts = 120  # 增加最大尝试次数（因为间隔变短）
        self.monitor_consecutive_failures = 0
        self.monitor_last_progress = -1
        self.monitor_last_status = None
        self.monitor_stable_count = 0  # 稳定状态计数
        self.monitor_task_id = task_id
        self.monitor_flow_id = flow_id
        
        # 开始监控，初始间隔0.5秒
        self.monitor_timer.start(500)  # 0.5秒间隔
        
        # 立即执行第一次查询
        QtCore.QTimer.singleShot(100, lambda: self._monitor_task_step(task_id, flow_id, main_panel))
    
    def _monitor_task_step(self, task_id, flow_id, main_panel):
        """单次任务监控步骤 - 优化版本"""
        self.monitor_attempt += 1
        print(f"🔄 第{self.monitor_attempt}次查询任务进度...")
        
        # 查询任务状态
        status_response = self.query_task_status(task_id, flow_id)
        if not status_response:
            self.monitor_consecutive_failures += 1
            print(f"❌ 第{self.monitor_attempt}次查询任务状态失败 (连续失败: {self.monitor_consecutive_failures})")
            
            # 更新进度条显示错误状态
            if main_panel:
                main_panel.update_task_progress(0, f"查询失败 ({self.monitor_consecutive_failures}/3)")
            
            # 如果连续失败超过3次，停止监控
            if self.monitor_consecutive_failures >= 3:
                print(f"⚠️ 连续失败{self.monitor_consecutive_failures}次，停止监控")
                self.show_error_message("任务监控失败，请手动检查任务状态")
                if main_panel:
                    main_panel.show_task_progress(False)
                self._stop_monitoring()
                return
            
            # 继续监控
            return
        
        # 重置连续失败计数
        self.monitor_consecutive_failures = 0
        
        # 获取任务状态和进度
        task_data = status_response.get("data", {})
        work_status = task_data.get("workStatus", 0)
        work_current = task_data.get("workCurrent", 0)
        work_number = task_data.get("workNumber", 100)
        
        # 状态映射（根据API文档修正）
        status_map = {
            0: "待处理",
            10: "运行中", 
            20: "已完成",
            30: "失败",
            40: "已取消"
        }
        status_text = status_map.get(work_status, f"未知状态({work_status})")
        
        # 使用API返回的总进度值
        if work_status == 20:  # 已完成
            progress = 100
        elif work_status == 10:  # 运行中
            # 直接使用workNumber作为总进度值
            progress = work_number if work_number > 0 else 0
        elif work_status == 0:  # 待处理
            progress = 0
        else:
            progress = 0
        
        print(f"📈 任务进度: {progress}% (状态: {status_text})")
        print(f"📊 详细信息: 等待人数{work_current}, API总进度{work_number}%, 状态码{work_status}")
        
        # 更新主界面进度条
        if main_panel:
            main_panel.update_task_progress(progress, status_text)
        
        # 智能间隔调整 - 基于状态稳定性
        current_state = (work_status, progress)
        if current_state == self.monitor_last_status:
            self.monitor_stable_count += 1
        else:
            self.monitor_stable_count = 0
            self.monitor_last_status = current_state
        
        # 如果任务完成
        if work_status == 20:
            print(f"🎉 任务完成！进度: {progress}%")
            
            # 获取任务详情和图片URL
            task_details = self.get_task_details(task_id)
            if task_details and task_details.get("data", {}).get("workUrl"):
                work_url = task_details["data"]["workUrl"]
                print(f"🖼️ 获取到图片URL: {work_url}")
                
                # 解析图片URL（可能是JSON字符串）
                try:
                    import json
                    if work_url.startswith('[') and work_url.endswith(']'):
                        # 如果是JSON数组格式
                        url_list = json.loads(work_url)
                        if url_list:
                            image_url = url_list[0]  # 取第一张图片
                            print(f"🖼️ 解析到图片地址: {image_url}")
                            
                            # 显示图片到主视角区域
                            self.display_result_image(image_url)
                        else:
                            print("❌ 图片URL列表为空")
                    else:
                        # 如果是单个URL字符串
                        print(f"🖼️ 单个图片地址: {work_url}")
                        self.display_result_image(work_url)
                except Exception as e:
                    print(f"❌ 解析图片URL失败: {str(e)}")
                    print(f"📋 原始URL: {work_url}")
            else:
                print("❌ 未获取到图片URL")
            
            self.show_success_message(f"任务完成！进度: {progress}%")
            if main_panel:
                main_panel.show_task_progress(False)
            
            # 立即停止监控，不再继续查询
            print("🛑 任务完成，停止监控")
            self._stop_monitoring()
            return
        
        # 检查是否进度很高但状态还是运行中（可能是API状态更新延迟）
        if work_status == 10 and progress >= 80:
            print(f"🔍 进度达到{progress}%但状态仍为运行中，主动检查任务详情...")
            
            # 主动获取任务详情检查是否有图片URL
            task_details = self.get_task_details(task_id)
            if task_details and task_details.get("data", {}).get("workUrl"):
                work_url = task_details["data"]["workUrl"]
                if work_url and work_url.strip():  # 如果有图片URL，说明任务已完成
                    print(f"🎉 发现任务已完成！获取到图片URL: {work_url}")
                    
                    # 解析图片URL（可能是JSON字符串）
                    try:
                        import json
                        if work_url.startswith('[') and work_url.endswith(']'):
                            # 如果是JSON数组格式
                            url_list = json.loads(work_url)
                            if url_list:
                                image_url = url_list[0]  # 取第一张图片
                                print(f"🖼️ 解析到图片地址: {image_url}")
                                
                                # 显示图片到主视角区域
                                self.display_result_image(image_url)
                            else:
                                print("❌ 图片URL列表为空")
                        else:
                            # 如果是单个URL字符串
                            print(f"🖼️ 单个图片地址: {work_url}")
                            self.display_result_image(work_url)
                    except Exception as e:
                        print(f"❌ 解析图片URL失败: {str(e)}")
                        print(f"📋 原始URL: {work_url}")
                    
                    self.show_success_message(f"任务完成！进度: {progress}%")
                    if main_panel:
                        main_panel.show_task_progress(False)
                    
                    # 立即停止监控，不再继续查询
                    print("🛑 任务完成，停止监控")
                    self._stop_monitoring()
                    return
                else:
                    print(f"⚠️ 进度{progress}%但未获取到图片URL，继续监控...")
            else:
                print(f"⚠️ 进度{progress}%但任务详情获取失败，继续监控...")
        
        # 如果任务失败
        if work_status in [30, 40]:
            print(f"❌ 任务失败，状态: {status_text}")
            self.show_error_message(f"任务失败，状态: {status_text}")
            if main_panel:
                main_panel.show_task_progress(False)
            
            # 立即停止监控，不再继续查询
            print("🛑 任务失败，停止监控")
            self._stop_monitoring()
            return
        
        # 检查是否超时
        if self.monitor_attempt >= self.monitor_max_attempts:
            print(f"⏰ 监控超时，已查询{self.monitor_max_attempts}次")
            self.show_error_message("任务监控超时，请手动检查任务状态")
            if main_panel:
                main_panel.show_task_progress(False)
            
            # 立即停止监控，不再继续查询
            print("🛑 监控超时，停止监控")
            self._stop_monitoring()
            return
        
        # 智能间隔调整 - 基于状态稳定性和进度
        if progress >= 80:  # 进度很高时，减少查询频率
            if self.monitor_stable_count >= 2:  # 稳定2次后增加间隔
                interval = 10000  # 高进度稳定状态10秒
            else:
                interval = 5000   # 高进度变化状态5秒
        elif self.monitor_stable_count >= 3:  # 状态稳定3次后增加间隔
            if progress < 10:
                interval = 3000   # 稳定状态3秒
            elif progress < 50:
                interval = 5000   # 稳定状态5秒
            else:
                interval = 8000   # 稳定状态8秒
        else:
            if progress < 10:
                interval = 1000   # 变化状态1秒
            elif progress < 50:
                interval = 2000   # 变化状态2秒
            else:
                interval = 3000   # 变化状态3秒
        
        # 更新定时器间隔
        self.monitor_timer.setInterval(interval)
        print(f"⏰ 下次查询间隔: {interval/1000}秒 (稳定计数: {self.monitor_stable_count})")
    
    def _stop_monitoring(self):
        """停止任务监控"""
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
            print("🛑 停止任务监控")
    
    def display_result_image(self, image_url):
        """显示结果图片到主视角区域"""
        try:
            print(f"🖼️ 开始下载并显示图片: {image_url}")
            
            # 下载图片
            import requests
            
            # 设置请求头，避免被拒绝
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            if response.status_code == 200:
                # 将图片数据转换为QPixmap
                image_data = QtCore.QByteArray(response.content)
                
                # 使用已经导入的QtGui
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_data)
                
                if not pixmap.isNull():
                    # 创建生成结果显示区域
                    if not hasattr(self, 'resultImageWidget'):
                        # 创建新的生成结果图片组件
                        self.resultImageWidget = ClickableImageView()
                        self.resultImageWidget.setMinimumHeight(220)
                        self.resultImageWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                        
                        # 添加到主布局中（在底部按钮区之前）
                        mainLayout = self.layout()
                        if mainLayout:
                            # 找到底部按钮区的位置
                            for i in range(mainLayout.count()):
                                widget = mainLayout.itemAt(i).widget()
                                if widget == self.bottomBtnContainer:
                                    mainLayout.insertWidget(i, self.resultImageWidget)
                                    break
                    
                    # 保存图片到临时文件，以便点击放大功能使用
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    temp_image_path = os.path.join(temp_dir, "generated_result.png")
                    pixmap.save(temp_image_path)
                    
                    # 显示生成的图片（显示点击提示）
                    self.resultImageWidget.setImage(pixmap, showOverlay=True)
                    self.resultImageWidget.currentImagePath = temp_image_path  # 设置图片路径
                    self.resultImageWidget.show()  # 确保显示
                    print(f"✅ 生成图片显示成功，尺寸: {pixmap.width()}x{pixmap.height()}")
                    print(f"✅ 图片已保存到: {temp_image_path}")
                    
                    # 更新按钮文本
                    if hasattr(self, 'captureBtn'):
                        self.captureBtn.setText("🖼️ 生成结果")
                else:
                    print("❌ 图片数据加载失败")
            else:
                print(f"❌ 下载图片失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 显示图片时出错: {str(e)}")
            import traceback
            print(f"📋 详细错误: {traceback.format_exc()}")
    
    def get_main_panel(self):
        """获取主界面引用"""
        try:
            # 通过父级查找主界面
            parent = self.parent()
            while parent:
                if hasattr(parent, 'show_task_progress'):
                    return parent
                parent = parent.parent()
            
            # 如果找不到，尝试通过全局变量
            global main_panel_instance
            if main_panel_instance and hasattr(main_panel_instance, 'show_task_progress'):
                return main_panel_instance
            
            return None
        except Exception as e:
            print(f"获取主界面引用失败: {str(e)}")
            return None
    
    def query_task_status(self, task_id, flow_id=None):
        """查询任务状态"""
        try:
            print(f"🔍 查询任务状态: {task_id}")
            
            # 根据API文档，使用GET请求，需要id和flowId参数
            params = {"id": task_id}
            if flow_id:
                params["flowId"] = flow_id
            
            response = self.call_api_request(API_ENDPOINTS["work_status"], params, method="GET")
            
            if response and response.get("code") == 0:
                print(f"✅ 任务状态查询成功")
                return response
            elif response:
                print(f"⚠️ 任务状态查询返回错误: {response.get('msg', '未知错误')}")
                return None
            else:
                print(f"❌ 查询任务状态失败，无响应")
                return None
                
        except Exception as e:
            print(f"❌ 查询任务状态异常: {str(e)}")
            return None
    
    def get_task_details(self, task_id):
        """获取任务详情"""
        try:
            print(f"📋 获取任务详情: {task_id}")
            
            # 根据API文档，使用GET请求，参数为id
            params = {"id": task_id}
            response = self.call_api_request(API_ENDPOINTS["work_details"], params, method="GET")
            
            if response and response.get("code") == 0:
                print(f"✅ 任务详情获取成功:")
                print(f"📥 详情数据: {json.dumps(response, ensure_ascii=False, indent=2)}")
                
                # 获取结果图片URL
                result_data = response.get("data", {})
                result_images = result_data.get("resultImages", [])
                if result_images:
                    print(f"🖼️ 生成结果图片:")
                    for i, img_url in enumerate(result_images):
                        print(f"  图片{i+1}: {img_url}")
                else:
                    print("⚠️ 未找到结果图片")
                
                return response
            else:
                error_msg = response.get("msg", "未知错误") if response else "网络错误"
                print(f"❌ 获取任务详情失败: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ 获取任务详情异常: {str(e)}")
            return None
    
    def upload_image(self, image_path):
        """上传图像到服务器"""
        try:
            print(f"📤 开始上传图像: {image_path}")
            
            if not os.path.exists(image_path):
                print(f"❌ 图像文件不存在: {image_path}")
                return None
                
            print(f"✅ 图像文件存在，开始上传...")
                
            with open(image_path, 'rb') as f:
                files = {'file': f}
                # 为文件上传使用正确的请求头，让requests自动设置Content-Type
                headers = {}
                login_data = get_auto_login_info()
                if login_data and login_data.get('token'):
                    headers["Authorization"] = f"Bearer {login_data.get('token')}"
                    print(f"🔐 使用Bearer token认证: {login_data.get('token')[:20]}...")
                
                upload_url = f"{API_BASE_URL}{API_ENDPOINTS['upload']}"
                print(f"🌐 上传URL: {upload_url}")
                print(f"📋 请求头: {headers}")
                
                response = requests.post(
                    upload_url, 
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                print(f"📥 上传响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📋 上传响应内容: {result}")
                    if result.get("code") == 0:
                        # 从正确的路径获取URL
                        image_url = result.get("data", {}).get("fileInfo", {}).get("fileUrl")
                        print(f"✅ 图像上传成功，URL: {image_url}")
                        return image_url
                    else:
                        print(f"❌ 图像上传失败: {result.get('msg', '未知错误')}")
                else:
                    print(f"❌ 图像上传HTTP错误: {response.status_code}")
                    print(f"📋 错误响应: {response.text}")
                    
        except Exception as e:
            print(f"❌ 图像上传异常: {str(e)}")
        return None
    
    def call_api_request(self, endpoint, params, method="POST"):
        """发送API请求"""
        try:
            # 构建请求URL
            url = f"{API_BASE_URL}{endpoint}"
            
            headers = self.get_auth_headers()
            
            if method.upper() == "GET":
                # GET请求：参数在URL中
                query_params = []
                for key, value in params.items():
                    if value is not None and value != "":
                        query_params.append(f"{key}={value}")
                
                if query_params:
                    url += "?" + "&".join(query_params)
                
                print(f"🌐 发送GET请求到: {url}")
                response = requests.get(url, headers=headers, timeout=30)
            else:
                # POST请求：参数在URL中
                query_params = []
                for key, value in params.items():
                    if value is not None and value != "":
                        query_params.append(f"{key}={value}")
                
                if query_params:
                    url += "?" + "&".join(query_params)
                
                print(f"🌐 发送POST请求到: {url}")
                response = requests.post(url, headers=headers, timeout=30)
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {str(e)}")
                    print(f"📋 原始响应: {response.text}")
                    return None
            else:
                print(f"❌ API请求HTTP错误: {response.status_code}")
                print(f"📋 错误响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API请求异常: {str(e)}")
            return None
    
    def get_auth_headers(self):
        """获取认证头"""
        # 尝试从登录响应中获取token
        try:
            # 从auto_login.json读取token
            login_data = get_auto_login_info()
            print(f"🔍 读取到的登录数据: {login_data}")
            
            if login_data and login_data.get('token'):
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Bearer {login_data.get('token')}"
                }
                print(f"🔐 使用Bearer token认证: {login_data.get('token')[:20]}...")
                return headers
            else:
                print("⚠️ 没有找到token，使用默认认证头")
                if login_data:
                    print(f"📋 登录数据内容: {list(login_data.keys())}")
                else:
                    print("📋 登录数据为空")
        except Exception as e:
            print(f"❌ 获取认证头异常: {str(e)}")
        
        # 如果没有token，使用默认认证头
        return {"Content-Type": "application/x-www-form-urlencoded"}
    
    def ensure_login(self):
        """确保已登录，如果未登录则尝试自动登录"""
        try:
            print("🔍 检查是否已登录...")
            
            # 从auto_login.json读取登录信息
            login_data = get_auto_login_info()
            if not login_data or not login_data.get('username'):
                print("❌ 没有保存的登录信息")
                return False
            
            username = login_data.get('username')
            password = login_data.get('password', '')
            
            print(f"📖 使用保存的登录信息: {username}")
            
            # 尝试登录
            login_params = {
                "username": username,
                "password": password
            }
            
            print("🔐 尝试自动登录...")
            response = self.call_api_request(API_ENDPOINTS["login"], login_params)
            
            if response and response.get("code") == 0:
                print("✅ 自动登录成功")
                return True
            else:
                error_msg = response.get("msg", "未知错误") if response else "网络错误"
                print(f"❌ 自动登录失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ 登录检查异常: {str(e)}")
            return False
    
    def get_uploaded_image_path(self):
        """获取用户上传的图像路径（用作参考图像）"""
        # 从上传组件获取图像路径
        print(f"🔍 检查uploadWidget: hasattr={hasattr(self, 'uploadWidget')}")
        if hasattr(self, 'uploadWidget'):
            print(f"🔍 uploadWidget存在: {self.uploadWidget}")
            if self.uploadWidget:
                image_path = getattr(self.uploadWidget, 'imagePath', None)
                print(f"🔍 从uploadWidget获取图像路径: {image_path}")
                return image_path
            else:
                print("❌ uploadWidget为None")
        else:
            print("❌ 没有找到uploadWidget组件")
        return None
    
    def get_reference_image_path(self):
        """获取参考图像路径（已废弃，现在使用用户上传的图像作为参考）"""
        return getattr(self, 'reference_image_path', None)
    
    def get_prompt_text(self):
        """获取提示词文本"""
        try:
            # 从当前选中的选项获取默认提示词
            current_option = self.comboBox.currentText()
            
            # 检查是否是多提示词选项
            if current_option in self.MULTI_PROMPT_DEFAULTS:
                # 多提示词选项，返回第一个提示词作为主要提示词
                multi_prompts = self.MULTI_PROMPT_DEFAULTS[current_option]
                prompt_text = multi_prompts[0] if multi_prompts else "默认提示词"
                print(f"📝 获取多提示词选项: {current_option}")
                print(f"📝 使用第一个提示词: {prompt_text}")
                return prompt_text
            else:
                # 单提示词选项
                prompt_text = self.PROMPT_DEFAULTS.get(current_option, "默认提示词")
                print(f"📝 获取单提示词: {prompt_text} (选项: {current_option})")
                return prompt_text
        except Exception as e:
            print(f"❌ 获取提示词失败: {str(e)}")
            return "默认提示词"
    
    def get_strength_value(self):
        """获取强度值"""
        try:
            # 从当前选中的选项获取默认强度值
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            strength_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("控制强度", 0.5)
            print(f"🎚️ 获取控制强度: {strength_value} (选项: {current_option})")
            return strength_value
        except Exception as e:
            print(f"❌ 获取控制强度失败: {str(e)}")
            return 0.5
    
    def get_weight_value(self):
        """获取权重值"""
        try:
            # 从当前选中的选项获取默认权重值
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            weight_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("参考图权重", 0.8)
            print(f"⚖️ 获取参考图权重: {weight_value} (选项: {current_option})")
            return weight_value
        except Exception as e:
            print(f"❌ 获取参考图权重失败: {str(e)}")
            return 0.8
    
    def get_start_value(self):
        """获取控制开始时间值"""
        try:
            # 从当前选中的选项获取默认开始时间
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            start_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("控制开始时间", 0.0)
            print(f"⏰ 获取控制开始时间: {start_value} (选项: {current_option})")
            return start_value
        except Exception as e:
            print(f"❌ 获取控制开始时间失败: {str(e)}")
            return 0.0
    
    def get_end_value(self):
        """获取控制结束时间值"""
        try:
            # 从当前选中的选项获取默认结束时间
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            end_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("控制结束时间", 1.0)
            print(f"⏰ 获取控制结束时间: {end_value} (选项: {current_option})")
            return end_value
        except Exception as e:
            print(f"❌ 获取控制结束时间失败: {str(e)}")
            return 1.0
    
    def get_multi_prompts(self):
        """获取多提示词列表"""
        try:
            current_option = self.comboBox.currentText()
            
            # 检查是否是多提示词选项
            if current_option in self.MULTI_PROMPT_DEFAULTS:
                multi_prompts = self.MULTI_PROMPT_DEFAULTS[current_option]
                print(f"📝 获取多提示词列表: {multi_prompts} (选项: {current_option})")
                return multi_prompts
            else:
                # 单提示词选项，返回包含单个提示词的列表
                single_prompt = self.get_prompt_text()
                print(f"📝 单提示词选项，返回: [{single_prompt}]")
                return [single_prompt]
        except Exception as e:
            print(f"❌ 获取多提示词失败: {str(e)}")
            return ["默认提示词"]
    
    def get_pixel_value(self):
        """获取像素值"""
        try:
            # 从当前选中的选项获取默认像素值
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            pixel_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("像素值", 0)
            print(f"📐 获取像素值: {pixel_value} (选项: {current_option})")
            return pixel_value
        except Exception as e:
            print(f"❌ 获取像素值失败: {str(e)}")
            return 0
    
    def get_is_vertical(self):
        """获取是否竖屏"""
        try:
            # 从当前选中的选项获取默认竖屏设置
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            is_vertical = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("是否竖屏", False)
            print(f"📱 获取竖屏设置: {is_vertical} (选项: {current_option})")
            return is_vertical
        except Exception as e:
            print(f"❌ 获取竖屏设置失败: {str(e)}")
            return False
    
    def get_enhance_value(self):
        """获取增强细节值"""
        try:
            # 从当前选中的选项获取默认增强值
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            enhance_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("增强细节", 0)
            print(f"🔍 获取增强细节: {enhance_value} (选项: {current_option})")
            return enhance_value
        except Exception as e:
            print(f"❌ 获取增强细节失败: {str(e)}")
            return 0
    
    def get_weight_one_value(self):
        """获取第二个权重值"""
        try:
            # 从当前选中的选项获取默认第二个权重值
            current_option = self.comboBox.currentText()
            work_type_key = f"{self.tabName}-{current_option}"
            weight_one_value = self.ADVANCED_DEFAULTS.get(work_type_key, {}).get("参考图权重2", 0.8)
            print(f"⚖️ 获取第二个权重值: {weight_one_value} (选项: {current_option})")
            return weight_one_value
        except Exception as e:
            print(f"❌ 获取第二个权重值失败: {str(e)}")
            return 0.8
    
    def show_success_message(self, message):
        """显示成功消息"""
        QtWidgets.QMessageBox.information(self, "成功", message)
    
    def show_error_message(self, message):
        """显示错误消息"""
        QtWidgets.QMessageBox.critical(self, "错误", message)

    def _expandInput(self):
        outer = QtWidgets.QHBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        inner = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("扩展像素")
        label.setStyleSheet("color: white; font-size: 14px;")
        spin = QtWidgets.QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(9999)
        spin.setValue(200)
        spin.setFixedWidth(140)
        spin.setStyleSheet("""
            background: #292929;
            color: #fff;
            border: 2px solid #3af;
            border-radius: 6px;
            font-size: 18px;
            padding: 4px 16px;
        """)
        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        inner.addWidget(label)
        inner.addWidget(spin)
        container = QtWidgets.QWidget()
        container.setLayout(inner)
        outer.addStretch(1)
        outer.addWidget(container)
        outer.addStretch(1)
        return outer

    def _addBottomBtn(self, btn):
        self.bottomBtnLayout.addStretch(1)
        self.bottomBtnLayout.addWidget(btn)
        self.bottomBtnLayout.addStretch(1)

    def crop_viewport_image(self, pixmap):
        """
        裁剪视口图片，去掉外围的UI元素
        """
        try:
            if pixmap.isNull():
                return None
            
            # 获取原始图片尺寸
            original_width = pixmap.width()
            original_height = pixmap.height()
            
            print(f"🔍 开始裁剪图片: {original_width} x {original_height}")
            
            # 定义裁剪参数（根据3ds Max视口的UI布局调整）
            # 这些值需要根据实际的3ds Max界面调整
            crop_margin = {
                'top': int(original_height * 0.08),      # 顶部8%
                'bottom': int(original_height * 0.08),   # 底部8%
                'left': int(original_width * 0.05),      # 左侧5%
                'right': int(original_width * 0.05)      # 右侧5%
            }
            
            # 计算裁剪区域
            crop_x = crop_margin['left']
            crop_y = crop_margin['top']
            crop_width = original_width - crop_margin['left'] - crop_margin['right']
            crop_height = original_height - crop_margin['top'] - crop_margin['bottom']
            
            # 确保裁剪区域有效
            if crop_width <= 0 or crop_height <= 0:
                print("⚠️ 裁剪区域无效，返回原图")
                return pixmap
            
            # 执行裁剪
            cropped = pixmap.copy(crop_x, crop_y, crop_width, crop_height)
            
            print(f"✅ 裁剪完成: {crop_width} x {crop_height}")
            print(f"📐 裁剪区域: x={crop_x}, y={crop_y}, w={crop_width}, h={crop_height}")
            
            return cropped
            
        except Exception as e:
            print(f"❌ 图片裁剪失败: {str(e)}")
            return None

    def capture_max_view(self):
        try:
            print("🔍 开始获取主视角视图...")
            
            # 尝试导入pymxs模块
            try:
                import pymxs
                print("✅ pymxs模块导入成功")
            except ImportError as e:
                print(f"❌ pymxs模块导入失败: {str(e)}")
                # 如果无法导入pymxs模块，显示一个消息框
                self.viewImageLabel.setText("获取视图功能需要在3ds Max环境中运行")
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Information)
                msgBox.setWindowTitle("提示")
                msgBox.setText("获取视图功能需要在3ds Max环境中运行")
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgBox.exec()
                return None
            
            # 如果成功导入pymxs模块，继续执行原来的代码
            import os
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), "quick_viewport_capture.png")
            ms_path = temp_path.replace('\\', '/')
            
            print(f"📁 临时文件路径: {temp_path}")
            print(f"📁 MaxScript路径: {ms_path}")
            
            # 执行截图代码
            rt = pymxs.runtime
            old_vp = rt.viewport.activeViewport
            print(f"📷 原激活视口: {old_vp}")
            
            # 在截图前隐藏UI元素
            print("🎯 开始隐藏UI元素...")
            hide_ui_code = '''
try (
    -- 隐藏ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已隐藏"
    
    -- 隐藏状态栏
    statusPanel.visible = false
    print "✅ 状态栏已隐藏"
    
    -- 隐藏命令面板（可选）
    -- actionMan.executeAction 0 "40140"
    -- print "✅ 命令面板已隐藏"
    
    print "🎯 UI元素隐藏完成"
) catch (
    print "⚠️ 隐藏UI元素时出现错误"
)
'''
            rt.execute(hide_ui_code)
            
            rt.viewport.activeViewport = 4  # 切换到右下角视口
            print("📷 切换到视口4")
            
            maxscript_code = f'''
try (
    local img = gw.getViewportDib()
    if img != undefined and img != null then (
        img.filename = "{ms_path}"
        save img
        close img
        print "截图保存成功"
    ) else (
        print "获取视口图像失败"
    )
) catch (
    print "截图过程中出现错误"
)
'''
            print(f"📝 执行MaxScript代码: {maxscript_code}")
            rt.execute(maxscript_code)
            
            rt.viewport.activeViewport = old_vp  # 恢复原激活视口
            print("📷 恢复原激活视口")
            
            # 截图完成后恢复UI元素
            print("🎯 开始恢复UI元素...")
            restore_ui_code = '''
try (
    -- 恢复ViewCube
    viewport.setLayout #layout_1
    print "✅ ViewCube已恢复"
    
    -- 恢复状态栏
    statusPanel.visible = true
    print "✅ 状态栏已恢复"
    
    -- 恢复命令面板（可选）
    -- actionMan.executeAction 0 "40140"
    -- print "✅ 命令面板已恢复"
    
    print "🎯 UI元素恢复完成"
) catch (
    print "⚠️ 恢复UI元素时出现错误"
)
'''
            rt.execute(restore_ui_code)
            
            # 加载图片
            if os.path.exists(temp_path):
                print(f"✅ 临时文件存在: {temp_path}")
                
                # 检查文件大小
                file_size = os.path.getsize(temp_path)
                print(f"📏 文件大小: {file_size} 字节")
                
                if file_size == 0:
                    print("❌ 文件大小为0，截图可能失败")
                    self.viewImageLabel.setText("截图失败，文件为空")
                    return None
                
                # 尝试加载图片
                pixmap = QtGui.QPixmap(temp_path)
                if not pixmap.isNull():
                    print("✅ 图片加载成功")
                    print(f"📐 图片尺寸: {pixmap.width()} x {pixmap.height()}")
                    
                    # 裁剪图片，去掉外围UI元素
                    cropped_pixmap = self.crop_viewport_image(pixmap)
                    if cropped_pixmap:
                        print("✅ 图片裁剪成功")
                        pixmap = cropped_pixmap
                        
                        # 保存裁剪后的图片到新文件
                        cropped_temp_path = os.path.join(tempfile.gettempdir(), "cropped_viewport_capture.png")
                        if pixmap.save(cropped_temp_path, "PNG"):
                            print(f"✅ 裁剪后图片已保存: {cropped_temp_path}")
                            # 更新返回路径为裁剪后的图片路径
                            temp_path = cropped_temp_path
                        else:
                            print("⚠️ 裁剪后图片保存失败，使用原图")
                    else:
                        print("⚠️ 图片裁剪失败，使用原图")
                    
                    # 使用隐藏的主视角图片组件处理图片（不显示在界面上）
                    self.viewImageWidget.setImagePath(temp_path, showOverlay=False)
                    print("✅ 主视角视图获取成功（已隐藏）")
                else:
                    print("❌ 图片加载失败")
                    # 尝试使用不同的方法加载
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(temp_path)
                        img_data = io.BytesIO()
                        img.save(img_data, format='PNG')
                        img_data.seek(0)
                        pixmap = QtGui.QPixmap()
                        pixmap.loadFromData(img_data.getvalue())
                        if not pixmap.isNull():
                            print("✅ 使用PIL加载图片成功")
                            scaled = pixmap.scaled(self.viewImageLabel.width(), self.viewImageLabel.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                            self.viewImageLabel.setPixmap(scaled)
                            self.viewImageLabel.setText("")
                        else:
                            print("❌ PIL加载也失败")
                            self.viewImageLabel.setText("图片格式不支持")
                    except ImportError:
                        print("❌ PIL模块不可用")
                        self.viewImageLabel.setText("图片格式不支持")
                    except Exception as e:
                        print(f"❌ PIL加载失败: {str(e)}")
                        self.viewImageLabel.setText("图片加载失败")
            else:
                print(f"❌ 临时文件不存在: {temp_path}")
                self.viewImageLabel.setText("未能获取视图")
                return None
            
            # 如果成功获取图像，返回图像路径
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                print(f"✅ 成功获取主视角视图: {temp_path}")
                return temp_path
            else:
                print("❌ 主视角视图获取失败")
                return None
        except Exception as e:
            # 捕获所有异常
            error_msg = f"获取视图时出错: {str(e)}"
            print(f"❌ {error_msg}")
            self.viewImageLabel.setText(error_msg)
            return None
            
        # 如果成功获取图像，返回图像路径
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print(f"✅ 成功获取主视角视图: {temp_path}")
            return temp_path
        else:
            print("❌ 主视角视图获取失败")
            return None

# =========================
# 登录窗口类
# =========================
class LoginWindow(QtWidgets.QWidget):
    # 定义登录成功信号
    loginSuccess = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.setWindowTitle("登录")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #222;")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        # 用户数据文件路径
        self.user_data_path = "user_data.json"
        
        # 创建UI元素
        self.createUI()
        
        # 创建默认账号（必须在创建UI元素之后）
        self.create_default_account()
        
        # 初始化主面板实例为None
        self.main_panel_instance = None
        
        # 自动填充用户名（如果current_username不是admin，则使用当前用户名）
        if current_username and current_username != "admin":
            self.usernameEdit.setText(current_username)
        else:
            self.usernameEdit.setText("")
        self.passwordEdit.setText("")
    
    def createUI(self):
        """创建UI元素"""
        # 创建布局
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(40, 40, 40, 40)
        mainLayout.setSpacing(20)
        
        # 标题
        titleLabel = QtWidgets.QLabel("Max Style Panel")
        titleLabel.setStyleSheet("""
            color: #3af;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        # 用户名输入
        usernameLayout = QtWidgets.QVBoxLayout()
        usernameLabel = QtWidgets.QLabel("用户名")
        usernameLabel.setStyleSheet("color: #fff; font-size: 14px;")
        self.usernameEdit = QtWidgets.QLineEdit()
        self.usernameEdit.setStyleSheet("""
            QLineEdit {
                background: #333;
                color: #fff;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3af;
            }
        """)
        self.usernameEdit.setPlaceholderText("请输入用户名")
        usernameLayout.addWidget(usernameLabel)
        usernameLayout.addWidget(self.usernameEdit)
        
        # 密码输入
        passwordLayout = QtWidgets.QVBoxLayout()
        passwordLabel = QtWidgets.QLabel("密码")
        passwordLabel.setStyleSheet("color: #fff; font-size: 14px;")
        self.passwordEdit = QtWidgets.QLineEdit()
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordEdit.setStyleSheet("""
            QLineEdit {
                background: #333;
                color: #fff;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3af;
            }
        """)
        self.passwordEdit.setPlaceholderText("请输入密码")
        passwordLayout.addWidget(passwordLabel)
        passwordLayout.addWidget(self.passwordEdit)
        
        # 登录按钮
        self.loginButton = QtWidgets.QPushButton("登录")
        self.loginButton.setStyleSheet("""
            QPushButton {
                background-color: #3da9fc;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                padding: 10px 0;
            }
            QPushButton:hover {
                background-color: #2176c1;
            }
            QPushButton:pressed {
                background-color: #174e85;
            }
        """)
        self.loginButton.clicked.connect(self.login)
        
        # 注册按钮
        self.registerButton = QtWidgets.QPushButton("注册")
        self.registerButton.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                padding: 10px 0;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        self.registerButton.clicked.connect(self.register)
        

        
        # 自动保存密码选项
        self.autoLoginCheck = QtWidgets.QCheckBox("自动保存密码")
        self.autoLoginCheck.setStyleSheet("""
            QCheckBox {
                color: #3da9fc;
                font-size: 14px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                border: 2px solid #3da9fc;
                border-radius: 3px;
                background-color: #222;
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:hover {
                border-color: #5dbdff;
                background-color: #333;
            }
            QCheckBox::indicator:checked {
                background-color: #3da9fc;
                border-color: #5dbdff;
                color: white;
                text-align: center;
                font-weight: bold;
                font-size: 10px;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #5dbdff;
                border-color: #5dbdff;
            }
        """)
        self.autoLoginCheck.setChecked(False)  # 默认不选中
        
        # 设置勾选时的文本
        self.autoLoginCheck.setProperty("checkedText", "✓")
        
        # 自动登录文件路径
        self.auto_login_file = "auto_login.json"
        
        # 状态消息
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setStyleSheet("color: #ccc; font-size: 14px;")  # 默认灰色
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        # 尝试自动登录（必须在statusLabel创建之后）
        self.try_auto_login()
        
        # 添加控件到布局
        mainLayout.addWidget(titleLabel)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(usernameLayout)
        mainLayout.addLayout(passwordLayout)
        mainLayout.addWidget(self.autoLoginCheck)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addSpacing(10)
        mainLayout.addWidget(self.loginButton)
        mainLayout.addWidget(self.registerButton)
        
        # 设置回车键触发登录
        self.passwordEdit.returnPressed.connect(self.login)
        
    def try_auto_login(self):
        """尝试自动登录"""
        print(f"🔍 检查自动登录文件: {self.auto_login_file}")
        if os.path.exists(self.auto_login_file):
            print("✅ 自动登录文件存在")
            try:
                with open(self.auto_login_file, 'r', encoding='utf-8') as f:
                    auto_login_data = json.load(f)
                print(f"📄 自动登录数据: {auto_login_data}")
                
                if auto_login_data.get("auto_login", False) and \
                   "username" in auto_login_data and "password" in auto_login_data:
                    
                    username = auto_login_data["username"]
                    password = auto_login_data["password"]
                    print(f"👤 自动登录用户: {username}")
                    
                    # 填充用户名和密码
                    self.usernameEdit.setText(username)
                    self.passwordEdit.setText(password)
                    
                    # 直接尝试API登录
                    print("🔄 尝试自动API登录...")
                    try:
                        params = {
                            "type": "10",  # 手机号+密码登录
                            "userPhone": username,
                            "password": password
                        }
                        
                        headers = {
                            "Content-Type": "application/x-www-form-urlencoded"
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}{API_ENDPOINTS['login']}",
                            data=params,
                            headers=headers,
                            timeout=10
                        )
                        
                        print(f"📡 API响应状态码: {response.status_code}")
                        print(f"📡 API响应内容: {response.text}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("code") == 0:
                                print("✅ 自动登录成功")
                                # 保存token到auto_login.json
                                try:
                                    token = result.get("data", {}).get("token")
                                    if token:
                                        # 更新auto_login.json，添加token
                                        auto_login_data["token"] = token
                                        with open(self.auto_login_file, 'w', encoding='utf-8') as f:
                                            json.dump(auto_login_data, f, ensure_ascii=False, indent=4)
                                        print(f"✅ Token已保存到auto_login.json")
                                except Exception as e:
                                    print(f"❌ 保存token失败: {str(e)}")
                                
                                # 不显示自动登录成功信息，直接进入主界面
                                self.loginSuccess.emit() # 发送登录成功信号
                                self.close() # 确保在信号发出后关闭窗口
                                return
                            else:
                                print(f"ℹ️ API登录失败: {result.get('msg', '未知错误')} - 静默失败，让用户手动登录")
                                # 不清除自动登录信息，也不显示错误，让用户手动登录
                                return
                        else:
                            print(f"ℹ️ API请求失败: {response.status_code} - 静默失败，让用户手动登录")
                            # 不清除自动登录信息，也不显示错误，让用户手动登录
                            return
                            
                    except Exception as e:
                        print(f"ℹ️ 自动API登录异常: {str(e)} - 静默失败，让用户手动登录")
                        # 不清除自动登录信息，也不显示错误，让用户手动登录
                        return
                        
                else:
                    print("❌ 自动登录数据格式不正确")
                    # 静默处理，不显示错误信息
                    return
                        
            except Exception as e:
                print(f"❌ 读取自动登录信息失败: {str(e)}")
                # 静默处理，不显示错误信息
                self.clear_auto_login_info() # 清除可能损坏的自动登录信息
        else:
            print("ℹ️ 自动登录文件不存在")
            # 静默处理，不显示错误信息
                
    def save_auto_login_info(self, username, password):
        """保存自动登录信息"""
        try:
            # 读取现有的auto_login.json，保留token
            auto_login_data = {}
            if os.path.exists(self.auto_login_file):
                with open(self.auto_login_file, 'r', encoding='utf-8') as f:
                    auto_login_data = json.load(f)
            
            # 更新登录信息，但保留token
            auto_login_data.update({
                "auto_login": self.autoLoginCheck.isChecked(),
                "username": username,
                "password": password if self.autoLoginCheck.isChecked() else "",  # 只有勾选时才保存密码
                "remember_checkbox": self.autoLoginCheck.isChecked()  # 记住复选框状态
            })
            
            with open(self.auto_login_file, 'w', encoding='utf-8') as f:
                json.dump(auto_login_data, f, ensure_ascii=False, indent=4)
            print(f"✅ 自动登录信息已保存: {auto_login_data}")
        except Exception as e:
            print(f"❌ 保存自动登录信息失败: {str(e)}")
            
    def clear_auto_login_info(self):
        """清除自动登录信息"""
        try:
            if os.path.exists(self.auto_login_file):
                os.remove(self.auto_login_file)
                print(f"✅ 自动登录信息已清除: {self.auto_login_file}")
            else:
                print(f"ℹ️ 自动登录文件不存在: {self.auto_login_file}")
        except Exception as e:
            print(f"❌ 清除自动登录信息失败: {str(e)}")
        
    def login(self):
        # 在函数开始时声明所有global变量
        global current_username, main_panel_instance
        
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text().strip()
        
        if not username or not password:
            self.statusLabel.setText("用户名和密码不能为空")
            return
        
        # 优先尝试API登录
        print("🔍 优先尝试API登录...")
        print(f"用户名: {username}")
        print(f"密码: {password}")
        print(f"API地址: {API_BASE_URL}{API_ENDPOINTS['login']}")
        
        try:
            params = {
                "type": "10",  # 手机号+密码登录
                "userPhone": username,
                "password": password
            }
            
            # 请求头
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            print("发送API请求...")
            response = requests.post(
                f"{API_BASE_URL}{API_ENDPOINTS['login']}", 
                data=params,
                headers=headers,
                timeout=30
            )
            
            print(f"HTTP状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                code = result.get("code")
                msg = result.get("msg", "未知错误")
                
                print(f"API返回: code={code}, msg={msg}")
                
                if code == 0:
                    # API登录成功
                    current_username = username
                    self.statusLabel.setText("API登录成功")
                    self.statusLabel.setStyleSheet("color: #55ff55; font-size: 14px;")  # 绿色
                    
                    # 保存token到auto_login.json
                    try:
                        token = result.get("data", {}).get("token")
                        if token:
                            # 读取现有的auto_login.json
                            auto_login_data = {}
                            if os.path.exists(self.auto_login_file):
                                with open(self.auto_login_file, 'r', encoding='utf-8') as f:
                                    auto_login_data = json.load(f)
                            
                            # 更新token
                            auto_login_data["token"] = token
                            auto_login_data["username"] = username
                            auto_login_data["password"] = password if self.autoLoginCheck.isChecked() else ""
                            auto_login_data["auto_login"] = self.autoLoginCheck.isChecked()
                            auto_login_data["remember_checkbox"] = self.autoLoginCheck.isChecked()
                            
                            # 保存到文件
                            with open(self.auto_login_file, 'w', encoding='utf-8') as f:
                                json.dump(auto_login_data, f, ensure_ascii=False, indent=4)
                            print(f"✅ Token已保存到auto_login.json: {token[:20]}...")
                    except Exception as e:
                        print(f"❌ 保存token失败: {str(e)}")
                    
                    # 始终保存账号信息，密码根据复选框状态决定
                        self.save_auto_login_info(username, password)
                    
                    self.close() # 关闭登录窗口
                    # 发送登录成功信号，触发主面板创建
                    self.loginSuccess.emit()
                    return
                elif code == -1:
                    # 异常情况
                    self.statusLabel.setText(f"登录异常: {msg}")
                    self.statusLabel.setStyleSheet("color: #ff5555; font-size: 14px;")  # 红色
                    print(f"API登录异常: {msg}")
                elif code == -1000:
                    # 请先登录/登录操作
                    self.statusLabel.setText(f"登录失败: {msg}")
                    self.statusLabel.setStyleSheet("color: #ff5555; font-size: 14px;")  # 红色
                    print(f"API登录失败: {msg}")
                else:
                    # 其他错误码
                    self.statusLabel.setText(f"登录失败: {msg}")
                    self.statusLabel.setStyleSheet("color: #ff5555; font-size: 14px;")  # 红色
                    print(f"API登录失败 (code={code}): {msg}")
                    # API登录失败，继续尝试网页Token获取
            else:
                print(f"API登录网络错误: {response.status_code}")
                # API登录失败，继续尝试网页Token获取
                
        except Exception as e:
            print(f"API登录调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # API登录失败，继续尝试网页Token获取
        
        # 所有登录方式都失败
        self.statusLabel.setText("登录失败，请检查用户名和密码")
        self.statusLabel.setStyleSheet("color: #ff5555; font-size: 14px;")  # 红色
    
    def register(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text().strip()
        
        if not username or not password:
            self.statusLabel.setText("用户名和密码不能为空")
            return
        
        # 检查用户数据文件是否存在，不存在则创建
        user_data = {}
        if os.path.exists(self.user_data_path):
            try:
                with open(self.user_data_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            except Exception as e:
                self.statusLabel.setText(f"读取用户数据失败: {str(e)}")
                return
        
        # 检查用户名是否已存在
        if username in user_data:
            self.statusLabel.setText("用户名已存在")
            return
        
        # 添加新用户
        password_hash = self.hash_password(password)
        user_data[username] = {
            "password_hash": password_hash,
            "register_time": QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
        }
        
        # 保存用户数据
        try:
            with open(self.user_data_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=4)
            self.statusLabel.setStyleSheet("color: #55ff55; font-size: 14px;")
            self.statusLabel.setText("注册成功，请登录")
        except Exception as e:
            self.statusLabel.setText(f"保存用户数据失败: {str(e)}")
    
    def hash_password(self, password):
        """简单的密码哈希函数"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def create_default_account(self):
        """创建默认账号"""
        # 默认账号信息
        default_username = "admin"
        default_password = "admin"
        
        # 确保用户数据目录存在
        data_dir = os.path.dirname(self.user_data_path)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except:
                pass
        
        # 如果用户数据文件不存在，创建它
        user_data = {}
        if os.path.exists(self.user_data_path):
            try:
                with open(self.user_data_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            except:
                pass
        
        # 如果默认账号不存在，添加它
        if default_username not in user_data:
            password_hash = self.hash_password(default_password)
            user_data[default_username] = {
                "password_hash": password_hash,
                "register_time": QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate),
                "is_default": True
            }
            
            # 保存用户数据
            try:
                with open(self.user_data_path, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"保存用户数据失败: {str(e)}")
            
        # 自动填充默认账号
        self.usernameEdit.setText(default_username)
        self.passwordEdit.setText(default_password)

    def showEvent(self, event):
        # 检查自动登录信息
        auto_info = get_auto_login_info()
        if auto_info and auto_info.get("username"):
            self.usernameEdit.setText(auto_info["username"])
            # 只有保存了密码时才填充密码
            if auto_info.get("password") and auto_info["password"]:
                self.passwordEdit.setText(auto_info["password"])
            # 恢复复选框状态
            if "remember_checkbox" in auto_info:
                self.autoLoginCheck.setChecked(auto_info["remember_checkbox"])
        else:
            # 如果没有自动登录信息，使用当前用户名或默认值
            if current_username and current_username != "admin":
                self.usernameEdit.setText(current_username)
            else:
                self.usernameEdit.setText("")
            # 默认不勾选复选框
            self.autoLoginCheck.setChecked(False)
        super(LoginWindow, self).showEvent(event)

# =========================
# 主面板类（多Tab）
# =========================
class MaxStylePanelQt(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MaxStylePanelQt, self).__init__(parent)
        # 直接启用主面板，不再检查登录状态
        self.setEnabled(True)
        try:
            self.setWindowTitle("PS风格面板")
            self.resize(600, 760)  # 初始高度调大
            self.setStyleSheet("background-color: #222;")
            mainLayout = QtWidgets.QVBoxLayout(self)
            mainLayout.setContentsMargins(30, 30, 30, 30)
            mainLayout.setSpacing(18)
            
            # 顶部栏（用户名和退出按钮）
            topBarLayout = QtWidgets.QHBoxLayout()
            
            # 左侧标题
            titleLabel = QtWidgets.QLabel("PS风格面板")
            titleLabel.setStyleSheet("""
                color: white;
                font-size: 20px;
                font-weight: bold;
            """)
            
            # 右侧用户信息和退出按钮
            userInfoLayout = QtWidgets.QHBoxLayout()
            
            # 用户头像（使用圆形背景色）
            self.userAvatar = QtWidgets.QLabel()
            self.userAvatar.setFixedSize(32, 32)
            self.userAvatar.setStyleSheet("""
                background-color: #3da9fc;
                border-radius: 16px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            """)
            self.userAvatar.setAlignment(QtCore.Qt.AlignCenter)
            self.userAvatar.setText("A")
            
            # 用户名
            self.usernameLabel = QtWidgets.QLabel("admin")
            self.usernameLabel.setStyleSheet("""
                color: white;
                font-size: 14px;
                margin-left: 5px;
            """)
            
            # 积分显示
            self.pointsLabel = QtWidgets.QLabel("🎯 1000")
            self.pointsLabel.setStyleSheet("""
                color: #ffd700;
                font-size: 12px;
                font-weight: bold;
                margin-left: 8px;
                padding: 2px 6px;
                background-color: rgba(255, 215, 0, 0.1);
                border-radius: 4px;
            """)
            
            # 用户信息按钮
            userInfoButton = QtWidgets.QPushButton("👤")
            userInfoButton.setFixedSize(28, 28)
            userInfoButton.setStyleSheet("""
                QPushButton {
                    background-color: #3da9fc;
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2176c1;
                }
                QPushButton:pressed {
                    background-color: #174e85;
                }
            """)
            userInfoButton.setCursor(QtCore.Qt.PointingHandCursor)
            userInfoButton.clicked.connect(self.show_user_info_from_button)
            
            # 退出按钮
            logoutButton = QtWidgets.QPushButton("退出登录")
            logoutButton.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #3da9fc;
                    border: none;
                    font-size: 14px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    color: #5dbdff;
                    text-decoration: underline;
                }
            """)
            logoutButton.setCursor(QtCore.Qt.PointingHandCursor)
            logoutButton.clicked.connect(self.logout)
            
            # 添加到用户信息布局
            userInfoLayout.addWidget(self.userAvatar)
            userInfoLayout.addWidget(self.usernameLabel)
            userInfoLayout.addWidget(self.pointsLabel)
            userInfoLayout.addWidget(userInfoButton)
            userInfoLayout.addWidget(logoutButton)
            userInfoLayout.setSpacing(8)
            
            # 添加到顶部栏
            topBarLayout.addWidget(titleLabel)
            topBarLayout.addStretch(1)
            topBarLayout.addLayout(userInfoLayout)
            
            # 添加顶部栏到主布局
            mainLayout.addLayout(topBarLayout)
            
            # 添加分隔线
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.HLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            separator.setStyleSheet("background-color: #444;")
            separator.setFixedHeight(1)
            mainLayout.addWidget(separator)
            
            # 任务进度条区域
            self.taskProgressWidget = QtWidgets.QWidget()
            self.taskProgressWidget.setVisible(False)  # 默认隐藏
            self.taskProgressWidget.setStyleSheet("""
                QWidget {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            
            taskProgressLayout = QtWidgets.QVBoxLayout(self.taskProgressWidget)
            taskProgressLayout.setContentsMargins(15, 15, 15, 15)
            taskProgressLayout.setSpacing(10)
            
            # 任务状态标签
            self.taskStatusLabel = QtWidgets.QLabel("准备中...")
            self.taskStatusLabel.setStyleSheet("""
                color: #3da9fc;
                font-size: 14px;
                font-weight: bold;
            """)
            self.taskStatusLabel.setAlignment(QtCore.Qt.AlignCenter)
            
            # 进度条
            self.taskProgressBar = QtWidgets.QProgressBar()
            self.taskProgressBar.setMinimum(0)
            self.taskProgressBar.setMaximum(100)
            self.taskProgressBar.setValue(0)
            self.taskProgressBar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #444;
                    border-radius: 6px;
                    text-align: center;
                    font-weight: bold;
                    color: white;
                    background-color: #1a1a1a;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #3da9fc, stop:0.5 #2176c1, stop:1 #174e85);
                    border-radius: 4px;
                }
            """)
            
            # 进度百分比标签
            self.taskProgressLabel = QtWidgets.QLabel("0%")
            self.taskProgressLabel.setStyleSheet("""
                color: #ffd700;
                font-size: 12px;
                font-weight: bold;
            """)
            self.taskProgressLabel.setAlignment(QtCore.Qt.AlignCenter)
            
            # 取消按钮
            self.taskCancelButton = QtWidgets.QPushButton("取消任务")
            self.taskCancelButton.setFixedHeight(28)
            self.taskCancelButton.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            self.taskCancelButton.clicked.connect(self.cancel_task)
            
            # 添加到进度条布局
            taskProgressLayout.addWidget(self.taskStatusLabel)
            taskProgressLayout.addWidget(self.taskProgressBar)
            taskProgressLayout.addWidget(self.taskProgressLabel)
            taskProgressLayout.addWidget(self.taskCancelButton)
            
            # 添加任务进度条到主布局
            mainLayout.addWidget(self.taskProgressWidget)
            
            # 主Tab控件
            self.tabWidget = QtWidgets.QTabWidget()
        except Exception as e:
            import traceback
            error_msg = f"初始化主面板时出错: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            # 显示一个简单的错误消息
            errorLabel = QtWidgets.QLabel(f"初始化失败: {str(e)}")
            errorLabel.setStyleSheet("color: red; font-size: 16px;")
            errorLayout = QtWidgets.QVBoxLayout(self)
            errorLayout.addWidget(errorLabel)
            return
        self.tabWidget.setStyleSheet("""
QTabBar::tab {
    min-width: 70px;
    min-height: 32px;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 1.5px;
    color: #bbb;
    background: #222;
    border: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 2px;
    padding: 6px 8px 6px 8px;
    transition: background 0.2s;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3da9fc, stop:1 #2176c1);
    color: #fff;
    border-bottom: 2px solid #3af;
    box-shadow: 0px 2px 8px #3af;
}
QTabBar::tab:hover {
    background: #333;
    color: #3af;
}
QTabWidget::pane {
    border: 1px solid #444;
    top: -1px;
    border-radius: 12px;
    background: #222;
}
""")
        try:
            tabNames = ["室内设计", "建筑规划", "景观设计", "图像处理"]
            for name in tabNames:
                try:
                    tab = QtWidgets.QWidget()
                    tabLayout = QtWidgets.QVBoxLayout(tab)
                    tabLayout.setContentsMargins(0, 0, 0, 0)
                    tabLayout.setSpacing(0)
                    tabContent = TabContentWidget(name)
                    tabLayout.addWidget(tabContent)
                    tab.setLayout(tabLayout)
                    self.tabWidget.addTab(tab, name)
                except Exception as e:
                    import traceback
                    error_msg = f"添加Tab '{name}'时出错: {str(e)}\n{traceback.format_exc()}"
                    print(error_msg)
                    # 添加一个错误Tab
                    errorTab = QtWidgets.QWidget()
                    errorLayout = QtWidgets.QVBoxLayout(errorTab)
                    errorLabel = QtWidgets.QLabel(f"Tab '{name}'加载失败: {str(e)}")
                    errorLabel.setStyleSheet("color: red; font-size: 16px;")
                    errorLayout.addWidget(errorLabel)
                    self.tabWidget.addTab(errorTab, f"{name}(错误)")
            mainLayout.addWidget(self.tabWidget)
            self.setLayout(mainLayout)
        except Exception as e:
            import traceback
            error_msg = f"添加Tabs时出错: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            # 显示一个简单的错误消息
            errorLabel = QtWidgets.QLabel(f"添加Tabs失败: {str(e)}")
            errorLabel.setStyleSheet("color: red; font-size: 16px;")
            errorLayout = QtWidgets.QVBoxLayout(self)
            errorLayout.addWidget(errorLabel)
            self.setLayout(errorLayout)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        # 不再尝试获取3ds Max主窗口
        self.main_win = None
        
        # 请求用户信息但不显示弹窗，只更新积分显示
        self.request_user_info_silent()

    def request_user_info_silent(self):
        """静默请求用户信息，只更新积分显示，不显示弹窗"""
        try:
            print("🔍 静默请求用户信息...")
            
            # 从auto_login.json获取token
            try:
                with open("auto_login.json", 'r', encoding='utf-8') as f:
                    login_data = json.load(f)
                    token = login_data.get("token", "")
                    username = login_data.get("username", "admin")
                    print(f"📋 获取到用户: {username}")
            except Exception as e:
                print(f"❌ 读取登录信息失败: {str(e)}")
                token = ""
                username = "admin"
            
            # 模拟用户信息（因为API暂时不可用）
            user_info = {
                "username": username,
                "userId": "12345",
                "phone": "13594226812",
                "points": 1000,  # 积分
                "balance": 500,   # 余额
                "credits": 200,   # 信用点
                "vipLevel": 1,    # VIP等级
                "lastLogin": "2024-12-01 10:30:00"
            }
            
            # 只更新积分显示，不显示弹窗
            self.update_points_display(user_info.get("points", 0))
            print("✅ 静默更新积分显示完成")
            
        except Exception as e:
            print(f"❌ 静默请求用户信息失败: {str(e)}")

    def request_user_info(self):
        """请求用户信息并显示弹窗"""
        try:
            print("🔍 请求用户信息...")
            
            # 从auto_login.json获取token
            try:
                with open("auto_login.json", 'r', encoding='utf-8') as f:
                    login_data = json.load(f)
                    token = login_data.get("token", "")
                    username = login_data.get("username", "admin")
                    print(f"📋 获取到用户: {username}")
            except Exception as e:
                print(f"❌ 读取登录信息失败: {str(e)}")
                token = ""
                username = "admin"
            
            # 模拟用户信息（因为API暂时不可用）
            user_info = {
                "username": username,
                "userId": "12345",
                "phone": "13594226812",
                "points": 1000,  # 积分
                "balance": 500,   # 余额
                "credits": 200,   # 信用点
                "vipLevel": 1,    # VIP等级
                "lastLogin": "2024-12-01 10:30:00"
            }
            
            # 更新积分显示
            self.update_points_display(user_info.get("points", 0))
            
            # 显示用户信息弹窗
            self.show_user_info_dialog(user_info)
            
        except Exception as e:
            print(f"❌ 请求用户信息失败: {str(e)}")
            # 显示错误信息
            self.show_error_dialog("获取用户信息失败", str(e))

    def show_user_info_from_button(self):
        """从用户信息按钮点击显示用户信息"""
        try:
            print("🔍 从按钮点击显示用户信息...")
            
            # 从auto_login.json获取用户信息
            try:
                with open("auto_login.json", 'r', encoding='utf-8') as f:
                    login_data = json.load(f)
                    username = login_data.get("username", "admin")
            except Exception as e:
                print(f"❌ 读取登录信息失败: {str(e)}")
                username = "admin"
            
            # 模拟用户信息
            user_info = {
                "username": username,
                "userId": "12345",
                "phone": "13594226812",
                "points": 1000,  # 积分
                "balance": 500,   # 余额
                "credits": 200,   # 信用点
                "vipLevel": 1,    # VIP等级
                "lastLogin": "2024-12-01 10:30:00"
            }
            
            # 显示用户信息弹窗
            self.show_user_info_dialog(user_info)
            
        except Exception as e:
            print(f"❌ 显示用户信息失败: {str(e)}")
            self.show_error_dialog("显示用户信息失败", str(e))

    def update_points_display(self, points):
        """更新积分显示"""
        try:
            if hasattr(self, 'pointsLabel'):
                self.pointsLabel.setText(f"🎯 {points}")
                print(f"✅ 更新积分显示: {points}")
        except Exception as e:
            print(f"❌ 更新积分显示失败: {str(e)}")

    def show_user_info_dialog(self, user_info):
        """显示用户信息弹窗"""
        try:
            # 创建弹窗
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("用户信息")
            dialog.setFixedSize(400, 300)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2a2a2a;
                    color: white;
                }
                QLabel {
                    color: white;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #3da9fc;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2176c1;
                }
                QPushButton:pressed {
                    background-color: #174e85;
                }
            """)
            
            # 创建布局
            layout = QtWidgets.QVBoxLayout(dialog)
            layout.setSpacing(15)
            
            # 标题
            title_label = QtWidgets.QLabel("👤 用户信息")
            title_label.setStyleSheet("""
                color: #3da9fc;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
            """)
            title_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # 用户信息内容
            info_widget = QtWidgets.QWidget()
            info_layout = QtWidgets.QVBoxLayout(info_widget)
            info_layout.setSpacing(8)
            
            # 用户名
            username_label = QtWidgets.QLabel(f"📱 用户名: {user_info.get('username', 'N/A')}")
            info_layout.addWidget(username_label)
            
            # 用户ID
            userid_label = QtWidgets.QLabel(f"🆔 用户ID: {user_info.get('userId', 'N/A')}")
            info_layout.addWidget(userid_label)
            
            # 手机号
            phone_label = QtWidgets.QLabel(f"📞 手机号: {user_info.get('phone', 'N/A')}")
            info_layout.addWidget(phone_label)
            
            # 积分
            points_label = QtWidgets.QLabel(f"🎯 积分: {user_info.get('points', 0)}")
            points_label.setStyleSheet("color: #ffd700; font-weight: bold;")
            info_layout.addWidget(points_label)
            
            # 余额
            balance_label = QtWidgets.QLabel(f"💰 余额: {user_info.get('balance', 0)}")
            balance_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            info_layout.addWidget(balance_label)
            
            # 信用点
            credits_label = QtWidgets.QLabel(f"💎 信用点: {user_info.get('credits', 0)}")
            credits_label.setStyleSheet("color: #ff69b4; font-weight: bold;")
            info_layout.addWidget(credits_label)
            
            # VIP等级
            vip_label = QtWidgets.QLabel(f"👑 VIP等级: {user_info.get('vipLevel', 0)}")
            vip_label.setStyleSheet("color: #ff4500; font-weight: bold;")
            info_layout.addWidget(vip_label)
            
            # 最后登录时间
            last_login_label = QtWidgets.QLabel(f"🕒 最后登录: {user_info.get('lastLogin', 'N/A')}")
            info_layout.addWidget(last_login_label)
            
            layout.addWidget(info_widget)
            
            # 按钮
            button_layout = QtWidgets.QHBoxLayout()
            
            # 确定按钮
            ok_button = QtWidgets.QPushButton("确定")
            ok_button.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_button)
            
            # 刷新按钮
            refresh_button = QtWidgets.QPushButton("刷新")
            refresh_button.clicked.connect(lambda: self.refresh_user_info(dialog))
            button_layout.addWidget(refresh_button)
            
            layout.addLayout(button_layout)
            
            # 显示弹窗
            dialog.exec()
            
        except Exception as e:
            print(f"❌ 显示用户信息弹窗失败: {str(e)}")
            self.show_error_dialog("显示用户信息失败", str(e))

    def show_error_dialog(self, title, message):
        """显示错误弹窗"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #3da9fc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #2176c1;
            }
        """)
        msg_box.exec()

    def refresh_user_info(self, dialog):
        """刷新用户信息"""
        try:
            print("🔄 刷新用户信息...")
            # 这里可以重新请求API获取最新用户信息
            # 暂时使用模拟数据
            user_info = {
                "username": "admin",
                "userId": "12345",
                "phone": "13594226812",
                "points": 1200,  # 更新积分
                "balance": 600,   # 更新余额
                "credits": 250,   # 更新信用点
                "vipLevel": 1,
                "lastLogin": "2024-12-01 10:35:00"
            }
            
            # 关闭当前弹窗并显示新信息
            dialog.accept()
            self.show_user_info_dialog(user_info)
            
        except Exception as e:
            print(f"❌ 刷新用户信息失败: {str(e)}")
            self.show_error_dialog("刷新失败", str(e))

    # 获取3ds Max主窗口（用于Dock嵌入）- 简化版本，不再尝试导入MaxPlus
    def get_max_main_window(self):
        return None

    # 事件过滤器（主窗口激活时自动置顶）
    def eventFilter(self, obj, event):
        if obj == self.main_win and event.type() == QtCore.QEvent.WindowActivate:
            self.show()
            self.raise_()
        return super(MaxStylePanelQt, self).eventFilter(obj, event)
        
    # 退出登录
    def logout(self):
        global current_username, main_panel_instance
        
        print("执行退出登录操作...")
        # 清除自动登录设置
        # 创建一个临时的LoginWindow实例来清除自动登录信息
        temp_login = LoginWindow()
        temp_login.clear_auto_login_info()
        print("已清除自动登录设置")
        # 不清除用户名，保持当前用户名
        print(f"保持当前用户名: {current_username}")
        # 关闭主面板
        print("关闭主面板...")
        self.close()
        # 创建并显示登录窗口
        print("创建登录窗口...")
        global login_dialog
        login_dialog = LoginWindow()
        try:
            login_dialog.loginSuccess.connect(create_main_panel)
        except Exception as e:
            print(f"连接loginSuccess信号失败: {str(e)}")
        login_dialog.show()
        login_dialog.raise_()
        print("登录窗口已显示")

    def show_task_progress(self, show=True):
        """显示或隐藏任务进度条"""
        self.taskProgressWidget.setVisible(show)
        if not show:
            # 重置进度条
            self.taskProgressBar.setValue(0)
            self.taskProgressLabel.setText("0%")
            self.taskStatusLabel.setText("准备中...")

    def update_task_progress(self, progress, status_text):
        """更新任务进度"""
        self.taskProgressBar.setValue(progress)
        self.taskProgressLabel.setText(f"{progress}%")
        self.taskStatusLabel.setText(status_text)

    def cancel_task(self):
        """取消当前任务"""
        # TODO: 实现任务取消功能
        self.show_task_progress(False)
        print("用户取消了任务")

def create_main_panel():
    global current_username, main_panel_instance
    username = current_username
    if main_panel_instance and main_panel_instance.isVisible():
        main_panel_instance.close()
        main_panel_instance.deleteLater()
        main_panel_instance = None
    main_panel_instance = MaxStylePanelQt(None)
    main_panel_instance.usernameLabel.setText(username)
    if username and len(username) > 0:
        main_panel_instance.userAvatar.setText(username[0].upper())
    main_panel_instance.show()
    main_panel_instance.raise_()
    return main_panel_instance





# =========================
# 脚本入口
# =========================
if __name__ == '__main__':
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    try:
        for w in QtWidgets.QApplication.allWidgets():
            if w.windowTitle() == u"多Tab演示面板（Qt版）" or w.windowTitle() == u"登录":
                w.close()
    except:
        pass
    parent = None
    
    # 启动时显示登录窗口
    login_dialog = LoginWindow()
    try:
        login_dialog.loginSuccess.connect(create_main_panel)
    except Exception as e:
        print(f"连接loginSuccess信号失败: {str(e)}")
    login_dialog.show()
    login_dialog.raise_()
    
    if not QtWidgets.QApplication.instance():
        import sys
        sys.exit(app.exec())