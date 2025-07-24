# -*- coding: utf-8 -*-
# MaxStylePanelQt.py
# 3ds Max PySide2 现代化多Tab面板
# 直接在3ds Max的Python窗口运行即可

import os
import json
import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import QUrl
from PySide2.QtGui import QDesktopServices

# 全局变量
current_username = "admin"  # 保存当前登录的用户名
login_window_instance = None  # 保存登录窗口实例
main_panel_instance = None  # 保存主面板实例

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_token.txt")

# 本地token HTTP服务
class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/token?value='):
            token = self.path.split('=')[1]
            if token:
                with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                    f.write(token)
            else:
                # token为空时删除本地token文件
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

def start_token_server():
    def run():
        try:
            server = HTTPServer(('127.0.0.1', 5000), TokenHandler)
            server.serve_forever()
        except Exception as e:
            print(f"Token HTTP服务启动失败: {e}")
    threading.Thread(target=run, daemon=True).start()

# 检查本地token
def is_logged_in():
    return os.path.exists(TOKEN_FILE)

def open_web_login():
    QDesktopServices.openUrl(QUrl("http://192.168.1.134:81/"))
    QtWidgets.QMessageBox.information(None, "登录引导", "请在弹出的网页中完成登录，登录成功后返回插件页面。\n\n网页端会自动写入本地token，无需手动操作。")

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
        "室内-多角度(白模)": [
            "书房，现代风格，书桌",
            "卧室，现代风格",
            "客厅，现代风格"
        ],
        "室内-多角度(线稿)": [
            "卧室，现代风格",
            "客厅，现代风格",
            "书房，现代风格"
        ],
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
        "彩平图": "彩平图",
        "毛坯房出图": "客厅,复古法式风格，金属茶几，沙发，地毯，装饰品，阳台，极精细的细节，吊灯",
        "线稿出图": "卧室，现代风格",
        "风格转换": "客厅，中式风格，",
        "白模渲染": "卧室，现代风格，电脑，书，电脑椅",
        "室内-多角度(白模)": "书房，现代风格，书桌",
        "室内-多角度(线稿)": "卧室，现代风格",
        # 建筑规划
        "彩平图": "建筑彩平图",
        "现场出图": "建筑工地，现代风格",
        "线稿出图": "建筑线稿，简约风格",
        "白模透视（精确）": "建筑白模，精确透视",
        "白模透视（体块）": "建筑体块白模，鸟瞰",
        "白模鸟瞰（精确）": "建筑鸟瞰，精确建模",
        "白模鸟瞰（体块）": "建筑鸟瞰，体块模型",
        "白天变夜景": "夜景，灯光渲染",
        "亮化工程": "建筑亮化，灯光设计",
        # 景观设计
        "彩平图": "景观彩平图",
        "现场出图": "景观现场，现代风格",
        "现场（局部）参考局部": "局部景观，参考对比",
        "线稿出图": "景观线稿，简约风格",
        "白模（透视）": "景观白模，透视效果",
        "白模（鸟瞰）": "景观鸟瞰，白模",
        "白天转夜景": "夜景，灯光渲染",
        "亮化工程": "景观亮化，灯光设计",
        # 图像处理
        "指定换材质": "替换为新材质",
        "修改局部": "局部修改，细节增强",
        "AI去除万物": "去除指定物体",
        "AI去水印": "去除水印",
        "增加物体": "添加新物体",
        "增加物体（指定物体）": "添加指定物体",
        "替换（产品）": "产品替换",
        "替换（背景天花）": "替换背景或天花板",
        "扩图": "扩展画面",
        "洗图": "图像清洗，去噪",
        "图像增强": "图像增强，细节提升",
        "溶图（局部）": "局部溶图，融合效果",
        "放大出图": "图像放大，高清",
        "老照片修复": "老照片修复，去划痕"
    }
    ADVANCED_DEFAULTS = {
        "室内-彩平图": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-多角度(白模)": {"控制强度": 0.58, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-多角度(线稿)": {"控制强度": 0.58, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-精准白模": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-精准白模（多风格）": {"控制强度": 0.58, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-线稿出图": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-线稿出图（多风格）": {"控制强度": 0.58, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-毛坯房": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-风格转换": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "室内-360出图": {"控制强度": 0.55, "参考图权重": 0.8, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-彩平图": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-白模透视(体块)": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-白模透视(精确)": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-白模鸟瞰(体块)": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-白模鸟瞰（精确）": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-白天变夜景": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-现场毛坯出图": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-亮化工程": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "建筑-线稿出图": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-彩平图": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-白模(透视)": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-白模（鸟瞰）": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-白天转夜景": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-亮化工程": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-线稿出图": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-现场（局部）": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1},
        "景观-现场（局部）参考局部": {"控制强度": 0.8, "参考图权重": 0.6, "控制开始时间": 0, "控制结束时间": 1}
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
        # 主标题美化
        self.titleLabel.setStyleSheet("""
color: #fff;
font-size: 24px;
font-weight: bold;
letter-spacing: 2px;
text-align: center;
text-shadow: 1px 1px 4px #000;
""")
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
        # 获取主视角按钮和显示区
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
        self.viewImageLabel = QtWidgets.QLabel()
        self.viewImageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.viewImageLabel.setMinimumHeight(220)
        self.viewImageLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.viewImageLabel.setStyleSheet("background-color: #222; border: 1px solid #444;")
        self.viewImageLabel.setText("未获取到视图")
        self.captureBtn.clicked.connect(self.capture_max_view)
        self.captureBtn.setEnabled(True)
        mainLayout.addWidget(self.captureBtn)
        mainLayout.addWidget(self.viewImageLabel)
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
                    widget = self.UploadWithPromptWidget(upload_label, prompt_label, prompt_default)
                    self.dynamicLayout.addWidget(widget)
                    if i < len(config) - 1:
                        self.dynamicLayout.addSpacing(12)
            else:
                # 默认3组上传区+提示词
                for i in range(3):
                        upload_label = f"参考图像{i+1}"
                        prompt_label = f"提示词{i+1}"
                        prompt_default = self.MULTI_PROMPT_DEFAULTS.get(option, ["", "", ""])[i]
                        widget = self.UploadWithPromptWidget(upload_label, prompt_label, prompt_default)
                        self.dynamicLayout.addWidget(widget)
                if i < 2:
                    self.dynamicLayout.addSpacing(12)
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
        else:
            # 单上传区+单提示词
            widget = self.UploadWithPromptWidget("参考图像", "提示词", self.PROMPT_DEFAULTS.get(option, ""))
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
            self.uploadWidget = ImageUploadWidget(uploadContainer)
            self.uploadWidget.move(0, 0)
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
        tabWidget = self.parent()
        tabName = ""
        if tabWidget and hasattr(tabWidget, 'parent') and tabWidget.parent() and hasattr(tabWidget.parent(), 'tabWidget'):
            idx = tabWidget.parent().tabWidget.currentIndex()
            tabName = tabWidget.parent().tabWidget.tabText(idx)
        option = self.comboBox.currentText()
        # 分流到不同的API调用函数
        if tabName == "室内设计":
            self.call_api_interior(option)
        elif tabName == "建筑规划":
            self.call_api_architecture(option)
        elif tabName == "景观设计":
            self.call_api_landscape(option)
        elif tabName == "图像处理":
            self.call_api_image(option)
        else:
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
        print("调用室内设计-彩平图API")
        # TODO: 填写API实现
        pass
    def api_interior_mao_pi_fang(self):
        print("调用室内设计-毛坯房出图API")
        pass
    def api_interior_xian_gao(self):
        print("调用室内设计-线稿出图API")
        pass
    def api_interior_bai_mo(self):
        print("调用室内设计-白模渲染API")
        pass
    def api_interior_duo_fengge_baimo(self):
        print("调用室内设计-多风格（白模）API")
        pass
    def api_interior_duo_fengge_xiangao(self):
        print("调用室内设计-多风格（线稿）API")
        pass
    def api_interior_fengge_zhuanhuan(self):
        print("调用室内设计-风格转换API")
        pass
    def api_interior_360(self):
        print("调用室内设计-360出图API")
        pass

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
        print("调用建筑规划-彩平图API")
        pass
    def api_arch_xian_chang(self):
        print("调用建筑规划-现场出图API")
        pass
    def api_arch_xian_gao(self):
        print("调用建筑规划-线稿出图API")
        pass
    def api_arch_baimo_toushi_jingque(self):
        print("调用建筑规划-白模透视（精确）API")
        pass
    def api_arch_baimo_toushi_tikuai(self):
        print("调用建筑规划-白模透视（体块）API")
        pass
    def api_arch_baimo_niokan_jingque(self):
        print("调用建筑规划-白模鸟瞰（精确）API")
        pass
    def api_arch_baimo_niokan_tikuai(self):
        print("调用建筑规划-白模鸟瞰（体块）API")
        pass
    def api_arch_baitian_yejing(self):
        print("调用建筑规划-白天变夜景API")
        pass
    def api_arch_lianghua(self):
        print("调用建筑规划-亮化工程API")
        pass

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
        print("调用景观设计-彩平图API")
        pass
    def api_land_xian_chang(self):
        print("调用景观设计-现场出图API")
        pass
    def api_land_xian_chang_jubu(self):
        print("调用景观设计-现场（局部）参考局部API")
        pass
    def api_land_xian_gao(self):
        print("调用景观设计-线稿出图API")
        pass
    def api_land_baimo_toushi(self):
        print("调用景观设计-白模（透视）API")
        pass
    def api_land_baimo_niokan(self):
        print("调用景观设计-白模（鸟瞰）API")
        pass
    def api_land_baitian_yejing(self):
        print("调用景观设计-白天转夜景API")
        pass
    def api_land_lianghua(self):
        print("调用景观设计-亮化工程API")
        pass

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
        print("调用图像处理-指定换材质API")
        pass
    def api_img_xiugai_jubu(self):
        print("调用图像处理-修改局部API")
        pass
    def api_img_quchu(self):
        print("调用图像处理-AI去除万物API")
        pass
    def api_img_shuiyin(self):
        print("调用图像处理-AI去水印API")
        pass
    def api_img_zengjia(self):
        print("调用图像处理-增加物体API")
        pass
    def api_img_zengjia_zhiding(self):
        print("调用图像处理-增加物体（指定物体）API")
        pass
    def api_img_tihuan_chanpin(self):
        print("调用图像处理-替换（产品）API")
        pass
    def api_img_tihuan_beijing(self):
        print("调用图像处理-替换（背景天花）API")
        pass
    def api_img_kuotu(self):
        print("调用图像处理-扩图API")
        pass
    def api_img_xitu(self):
        print("调用图像处理-洗图API")
        pass
    def api_img_enhance(self):
        print("调用图像处理-图像增强API")
        pass
    def api_img_rongtu(self):
        print("调用图像处理-溶图（局部）API")
        pass
    def api_img_fangda(self):
        print("调用图像处理-放大出图API")
        pass
    def api_img_repair(self):
        print("调用图像处理-老照片修复API")
        pass

    def call_api_default(self, option):
        print(f"[API] 默认: {option}")
        # TODO: 其它情况的API调用
        pass

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

    def capture_max_view(self):
        try:
            # 尝试导入pymxs模块
            try:
                import pymxs
            except ImportError:
                # 如果无法导入pymxs模块，显示一个消息框
                self.viewImageLabel.setText("获取视图功能需要在3ds Max环境中运行")
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Information)
                msgBox.setWindowTitle("提示")
                msgBox.setText("获取视图功能需要在3ds Max环境中运行")
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgBox.exec_()
                return
            
            # 如果成功导入pymxs模块，继续执行原来的代码
            import os
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), "quick_viewport_capture.jpg")
            ms_path = temp_path.replace('\\', '/')
            
            # 执行截图代码
            rt = pymxs.runtime
            old_vp = rt.viewport.activeViewport
            rt.viewport.activeViewport = 4  # 切换到右下角视口
            rt.execute(f'''
try (
    local img = gw.getViewportDib()
    if img != undefined and img != null then (
        img.filename = "{ms_path}"
        save img
        close img
    )
) catch ()
''')
            rt.viewport.activeViewport = old_vp  # 恢复原激活视口
            
            # 加载图片
            if os.path.exists(temp_path):
                pixmap = QtGui.QPixmap(temp_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(self.viewImageLabel.width(), self.viewImageLabel.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    self.viewImageLabel.setPixmap(scaled)
                    self.viewImageLabel.setText("")
                else:
                    self.viewImageLabel.setPixmap(QtGui.QPixmap())
                    self.viewImageLabel.setText("未能加载图片")
            else:
                self.viewImageLabel.setText("未能获取视图")
        except Exception as e:
            # 捕获所有异常
            self.viewImageLabel.setText(f"获取视图时出错: {str(e)}")
            print(f"获取视图时出错: {str(e)}")

# =========================
# 登录窗口类
# =========================
class LoginWindow(QtWidgets.QWidget):
    # 在PySide2中，信号需要这样定义
    try:
        loginSuccess = QtCore.Signal()
    except AttributeError:
        # 如果Signal不存在，尝试使用QSignal
        try:
            loginSuccess = QtCore.QSignal()
        except AttributeError:
            # 如果QSignal也不存在，使用SIGNAL/SLOT机制
            print("警告：无法创建Signal，将使用旧式SIGNAL/SLOT机制")
            loginSuccess = None  # 将在__init__中使用SIGNAL
    
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.setWindowTitle("登录")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #222;")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        # 用户数据文件路径
        self.user_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")
        
        # 创建UI元素
        self.createUI()
        
        # 创建默认账号（必须在创建UI元素之后）
        self.create_default_account()
        
        # 初始化主面板实例为None
        self.main_panel_instance = None
        
        # 自动填充用户名
        auto_info = get_auto_login_info()
        if auto_info and auto_info.get("username"):
            self.usernameEdit.setText(auto_info["username"])
        else:
            self.usernameEdit.setText(current_username)
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
        
        # 自动登录选项
        self.autoLoginCheck = QtWidgets.QCheckBox("自动登录")
        self.autoLoginCheck.setStyleSheet("color: #fff; font-size: 14px;")
        self.autoLoginCheck.setChecked(True)  # 默认选中
        
        # 自动登录文件路径
        self.auto_login_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_login.json")
        
        # 尝试自动登录
        self.try_auto_login()
        
        # 状态消息
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setStyleSheet("color: #ff5555; font-size: 14px;")
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        
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
        if os.path.exists(self.auto_login_file):
            try:
                with open(self.auto_login_file, 'r', encoding='utf-8') as f:
                    auto_login_data = json.load(f)
                
                if auto_login_data.get("auto_login", False) and \
                   "username" in auto_login_data and "password_hash" in auto_login_data:
                    
                    username = auto_login_data["username"]
                    password_hash = auto_login_data["password_hash"]
                    
                    # 填充用户名和密码（如果需要）
                    self.usernameEdit.setText(username)
                    # 注意：这里不能直接填充密码，因为我们只保存了哈希值
                    # 如果需要自动填充密码，需要保存明文密码，但这不安全
                    # 或者在登录时直接使用哈希值验证
                    
                    # 模拟登录
                    print(f"尝试自动登录用户: {username}")
                    # 直接调用login方法，但需要确保login方法能处理这种情况
                    # 或者创建一个专门的auto_login方法
                    # 为了简化，我们直接调用login，但需要确保它能处理没有明文密码的情况
                    # 这里我们假设login方法会再次哈希输入的密码进行比较
                    
                    # 更好的做法是直接验证哈希值，而不是模拟输入
                    # 暂时不自动填充密码，只填充用户名，让用户输入密码
                    # self.login() # 不直接调用，因为需要明文密码
                    
                    # 检查用户数据文件是否存在
                    if not os.path.exists(self.user_data_path):
                        print("用户数据文件不存在，无法自动登录")
                        self.statusLabel.setText("用户数据文件不存在，无法自动登录")
                        return
                    
                    # 读取用户数据
                    try:
                        with open(self.user_data_path, 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                    except Exception as e:
                        print(f"读取用户数据失败: {str(e)}")
                        self.statusLabel.setText(f"读取用户数据失败: {str(e)}")
                        return
                    
                    if username in user_data and user_data[username]["password_hash"] == password_hash:
                        print("自动登录成功")
                        self.loginSuccess.emit() # 发送登录成功信号
                        self.close() # 确保在信号发出后关闭窗口
                    else:
                        print("自动登录失败，密码或用户不匹配")
                        self.statusLabel.setText("自动登录失败，密码或用户不匹配")
                        self.clear_auto_login_info() # 清除错误的自动登录信息
                        
            except Exception as e:
                print(f"读取自动登录信息失败: {str(e)}")
                self.clear_auto_login_info() # 清除可能损坏的自动登录信息
                
    def save_auto_login_info(self, username, password):
        """保存自动登录信息"""
        try:
            with open(self.auto_login_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "auto_login": True,
                    "username": username,
                    "password_hash": self.hash_password(password) # 保存密码哈希值
                }, f, ensure_ascii=False, indent=4)
            print("自动登录信息已保存")
        except Exception as e:
            print(f"保存自动登录信息失败: {str(e)}")
            
    def clear_auto_login_info(self):
        """清除自动登录信息"""
        try:
            if os.path.exists(self.auto_login_file):
                os.remove(self.auto_login_file)
                print("自动登录信息已清除")
        except Exception as e:
            print(f"清除自动登录信息失败: {str(e)}")
        
    def login(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text().strip()
        
        if not username or not password:
            self.statusLabel.setText("用户名和密码不能为空")
            return
        
        # 检查用户数据文件是否存在
        if not os.path.exists(self.user_data_path):
            self.statusLabel.setText("用户不存在，请先注册")
            return
        
        # 读取用户数据
        try:
            with open(self.user_data_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except Exception as e:
            self.statusLabel.setText(f"读取用户数据失败: {str(e)}")
            return
        
        # 验证用户名和密码
        if username in user_data:
            stored_password_hash = user_data[username]["password_hash"]
            input_password_hash = self.hash_password(password)
            
            if stored_password_hash == input_password_hash:
                self.statusLabel.setText("")
                # 修正：同步用户名到全局变量
                global current_username
                current_username = username
                # 自动登录逻辑
                if hasattr(self, 'autoLoginCheck') and self.autoLoginCheck.isChecked():
                    set_auto_login_info(username, input_password_hash)
                else:
                    clear_auto_login_info()
                self.loginSuccess.emit()  # 发送登录成功信号
                self.close() # 确保在信号发出后关闭窗口
            else:
                self.statusLabel.setText("密码错误")
        else:
            self.statusLabel.setText("用户不存在")
    
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
        auto_info = get_auto_login_info()
        if auto_info and auto_info.get("username"):
            self.usernameEdit.setText(auto_info["username"])
        else:
            self.usernameEdit.setText(current_username)
        self.passwordEdit.setText("")
        super(LoginWindow, self).showEvent(event)

# =========================
# 主面板类（多Tab）
# =========================
class MaxStylePanelQt(QtWidgets.QWidget):
    def __init__(self, parent=None):
        if not is_logged_in():
            open_web_login()
        super(MaxStylePanelQt, self).__init__(parent)
        if not is_logged_in():
            QtWidgets.QMessageBox.warning(None, "未登录", "请先在网页完成登录，登录后重启插件。")
            self.setEnabled(False)
        else:
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
        print("执行退出登录操作...")
        # 清除自动登录设置
        clear_auto_login_info()
        print("已清除自动登录设置")
        # 重置全局用户名变量
        global current_username, main_panel_instance, login_window_instance
        current_username = "admin"
        print(f"已重置用户名为: {current_username}")
        # 关闭主面板
        print("关闭主面板...")
        self.close()
        # 创建并显示登录窗口
        print("创建登录窗口...")
        login_window_instance = LoginWindow()
        try:
            login_window_instance.loginSuccess.connect(create_main_panel)
        except Exception as e:
            print(f"连接loginSuccess信号失败: {str(e)}")
        login_window_instance.show()
        login_window_instance.raise_()
        print("登录窗口已显示")

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

def get_auto_login_info():
    auto_login_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_login.json")
    if os.path.exists(auto_login_file):
        try:
            with open(auto_login_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def set_auto_login_info(username, password_hash):
    auto_login_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_login.json")
    with open(auto_login_file, 'w', encoding='utf-8') as f:
        json.dump({
            "auto_login": True,
            "username": username,
            "password_hash": password_hash
        }, f, ensure_ascii=False, indent=4)

def clear_auto_login_info():
    auto_login_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_login.json")
    if os.path.exists(auto_login_file):
        try:
            os.remove(auto_login_file)
        except Exception:
            pass

# =========================
# 脚本入口
# =========================
if __name__ == '__main__':
    start_token_server()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    try:
        for w in QtWidgets.QApplication.allWidgets():
            if w.windowTitle() == u"多Tab演示面板（Qt版）" or w.windowTitle() == u"登录":
                w.close()
    except:
        pass
    parent = None
    # 启动时直接判断token
    if is_logged_in():
        main_panel_instance = MaxStylePanelQt(parent)
        main_panel_instance.show()
        main_panel_instance.raise_()
    else:
        open_web_login()
        QtWidgets.QMessageBox.information(None, "登录引导", "请在弹出的网页中完成登录，登录后重启插件。\n\n网页端会自动写入本地token，无需手动操作。")
    if not QtWidgets.QApplication.instance():
        import sys
        sys.exit(app.exec_())