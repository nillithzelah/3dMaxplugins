# -*- coding: utf-8 -*-
# MaxStylePanelQt.py
# 3ds Max PySide2 现代化多Tab面板
# 直接在3ds Max的Python窗口运行即可

import os
from PySide2 import QtWidgets, QtCore, QtGui

class ImageUploadWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, custom_height=None):
        super(ImageUploadWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        height = custom_height if custom_height else 240
        self.setFixedSize(260, height)
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
        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        icon_h = height - 60 if height > 80 else 40
        self.iconLabel.setFixedSize(240, icon_h)  # 填满上传框
        self.iconLabel.setStyleSheet("color: #bbb; font-size: 15px;")
        self.iconLabel.setText("拖放文件到此处上传\n或点击选择文件")
        layout.addSpacing(8)  # 顶部只留8像素
        layout.addWidget(self.iconLabel)
        layout.addSpacing(8)  # 图片和文件名之间
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
        self.iconLabel.setPixmap(QtGui.QPixmap(":/qt-project.org/styles/commonstyle/images/dirclosed-128.png").scaled(240, icon_h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText("拖放文件到此处上传\n或点击选择文件")

    def mousePressEvent(self, event):
        self.openFileDialog()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "background-color: #505080;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("background-color: #505080;", ""))

    def dropEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("background-color: #505080;", ""))
        urls = event.mimeData().urls()
        if urls:
            filePath = urls[0].toLocalFile()
            self.setImage(filePath)

    def openFileDialog(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)")
        if filePath:
            self.setImage(filePath)

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
            self.iconLabel.setText("拖放文件到此处上传\n或点击选择文件")
            self.fileNameLabel.setText("")
            self.imagePath = None

class CollapsibleWidget(QtWidgets.QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
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

        self.contentArea = QtWidgets.QWidget()
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)
        self.contentArea.setStyleSheet("background: none;")

        self.toggleAnimation = QtCore.QPropertyAnimation(self.contentArea, b"maximumHeight")
        self.toggleAnimation.setDuration(180)
        self.toggleAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(-2)  # 标题和内容区更贴合
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggleButton)
        layout.addWidget(self.contentArea)

    def setContentLayout(self, contentLayout):
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = 0
        expandedHeight = contentLayout.sizeHint().height()
        self.toggleAnimation.setStartValue(collapsedHeight)
        self.toggleAnimation.setEndValue(expandedHeight)

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

# 递归清理layout的函数，确保所有子控件和子layout都能被删除
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

class TabContentWidget(QtWidgets.QWidget):
    def __init__(self, tabName, parent=None):
        super(TabContentWidget, self).__init__(parent)
        # 下拉栏选项映射
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
        # 主布局：comboBar（顶部悬浮）+内容滚动区+底部按钮区
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(self.titleLabel)
        # 获取主视角视图按钮和图片显示区
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
        mainLayout.addWidget(comboBar)
        mainLayout.addWidget(scroll)
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

    def clearDynamicContent(self):
        clearLayout(self.dynamicLayout)
        # 清空底部按钮区
        clearLayout(self.bottomBtnLayout)

    def updateDynamicUI(self, option):
        self.clearDynamicContent()
        # 动态设置顶部标题
        # 获取Tab名
        tabWidget = self.parent()
        tabName = ""
        if tabWidget and hasattr(tabWidget, 'parent') and tabWidget.parent() and hasattr(tabWidget.parent(), 'tabWidget'):
            idx = tabWidget.parent().tabWidget.currentIndex()
            tabName = tabWidget.parent().tabWidget.tabText(idx)
        optionText = self.comboBox.currentText()
        self.titleLabel.setText(optionText)
        # 室内设计
        if option == '360出图':
            # 只显示按钮
            self._addBottomBtn(self._generateBtn())
        elif option in ['彩平图', '毛坯房出图', '风格转换']:
            self.dynamicLayout.addWidget(self._uploadGroup())
            self.dynamicLayout.addLayout(self._promptInput())
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
            self._addBottomBtn(self._generateBtn())
        elif option in ['线稿出图', '白模渲染']:
            self.dynamicLayout.setSpacing(8)
            self.dynamicLayout.addLayout(self._promptInput())
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
            self._addBottomBtn(self._generateBtn())
        elif option in ['多风格（白模）', '多风格（线稿）']:
            for i in range(3):
                groupWidget = QtWidgets.QWidget()
                groupLayout = QtWidgets.QVBoxLayout(groupWidget)
                groupLayout.setContentsMargins(0, 0, 0, 0)
                groupLayout.setSpacing(6)
                groupLayout.addWidget(self._uploadGroup(multi=False, label_text=f"参考图像{i+1}"))
                groupLayout.addLayout(self._promptInput())
                self.dynamicLayout.addWidget(groupWidget)
                if i < 2:
                    self.dynamicLayout.addSpacing(12)  # 组间距
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
            self._addBottomBtn(self._generateBtn())
        # 建筑规划Tab、景观设计Tab、图像处理Tab
        elif option in ['彩平图', '现场出图', '线稿出图', '白模透视（精确）', '白模透视（体块）', '白模鸟瞰（精确）', '白模鸟瞰（体块）', '白天变夜景', '亮化工程', '白模（透视）', '白模（鸟瞰）', '白天转夜景']:
            self.dynamicLayout.addWidget(self._uploadGroup())
            self.dynamicLayout.addLayout(self._promptInput())
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
            self._addBottomBtn(self._generateBtn())
        elif option == '现场（局部）参考局部':
            self.dynamicLayout.addWidget(self._uploadGroup())
            self._addBottomBtn(self._generateBtn())
        # 图像处理Tab特殊分支
        elif option in ['AI去除万物', 'AI去水印', '图像增强', '放大出图', '老照片修复']:
            self._addBottomBtn(self._generateBtn())
        elif option == '扩图':
            self.dynamicLayout.addLayout(self._expandInput())
            self._addBottomBtn(self._generateBtn())
        elif option == '溶图（局部）':
            for i in range(2):
                groupWidget = QtWidgets.QWidget()
                groupLayout = QtWidgets.QVBoxLayout(groupWidget)
                groupLayout.setContentsMargins(0, 0, 0, 0)
                groupLayout.setSpacing(6)
                groupLayout.addWidget(self._uploadGroup(multi=False, label_text=f"参考图像{i+1}"))
                if i == 1:
                    groupLayout.addLayout(self._promptInput())
                self.dynamicLayout.addWidget(groupWidget)
                if i < 1:
                    self.dynamicLayout.addSpacing(12)
            self.dynamicLayout.addLayout(self._strengthSlider())
            self.dynamicLayout.addWidget(self._advancedParams())
            self._addBottomBtn(self._generateBtn())
        elif option in ['修改局部', '增加物体']:
            self.dynamicLayout.addLayout(self._promptInput())
            self._addBottomBtn(self._generateBtn())
        elif option in ['替换（产品）', '替换（背景天花）']:
            self.dynamicLayout.addWidget(self._uploadGroup())
            self._addBottomBtn(self._generateBtn())
        else:
            # 其它情况，上传区+提示词+控制强度+高级参数+按钮
            self.dynamicLayout.addWidget(self._uploadGroup())
            self.dynamicLayout.addLayout(self._promptInput())
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
            self.uploadTab = QtWidgets.QTabWidget(uploadContainer)
            self.uploadTab.setFixedSize(220, 36)
            self.uploadTab.setStyleSheet("QTabBar::tab { min-width: 100px; min-height: 32px; font-size: 14px; color: white; background: #444; border: 1px solid #555; border-bottom: none; } QTabBar::tab:selected { background: #222; color: #3af; border-bottom: 2px solid #3af; } QTabWidget::pane { border: none; }")
            self.uploadTab.addTab(QtWidgets.QWidget(), "自定义参考图")
            self.uploadTab.addTab(QtWidgets.QWidget(), "参考图片库")
            self.uploadTab.move(uploadContainer.width()-self.uploadTab.width(), 0)
            self.uploadWidget = ImageUploadWidget(uploadContainer)
            self.uploadWidget.move(0, 28)
            self.uploadTab.raise_()
            self.uploadWidget.raise_()
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
                tabWidget = QtWidgets.QTabWidget(uploadContainer)
                tabWidget.setFixedSize(220, 36)
                tabWidget.setStyleSheet("QTabBar::tab { min-width: 100px; min-height: 32px; font-size: 14px; color: white; background: #444; border: 1px solid #555; border-bottom: none; } QTabBar::tab:selected { background: #222; color: #3af; border-bottom: 2px solid #3af; } QTabWidget::pane { border: none; }")
                tabWidget.addTab(QtWidgets.QWidget(), "自定义参考图")
                tabWidget.addTab(QtWidgets.QWidget(), "参考图片库")
                tabWidget.move(uploadContainer.width()-tabWidget.width(), 0)
                uploadWidget = ImageUploadWidget(uploadContainer, custom_height=240)
                uploadWidget.move(0, 28)
                tabWidget.raise_()
                uploadWidget.raise_()
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

    def _promptInput(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(16, 0, 0, 0)  # 左边与上传区对齐
        layout.setSpacing(10)
        promptLabel = QtWidgets.QLabel("提示词")
        # 普通标签美化
        promptLabel.setStyleSheet("color: #ccc; font-size: 14px;")
        promptLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        promptEdit = QtWidgets.QLineEdit()
        promptEdit.setFixedWidth(180)
        # 输入框美化
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
        container = QtWidgets.QWidget()
        containerLayout = QtWidgets.QHBoxLayout(container)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(10)
        containerLayout.addWidget(promptLabel)
        containerLayout.addWidget(promptEdit)
        container.setFixedWidth(260)  # 与上传区宽度一致
        layout.addWidget(container)
        # layout.addStretch(1)  # 不再右侧拉伸
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
        return btn

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
        import os
        debug_dir = r'C:\Temp'
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
            f.write('回调已触发\n')
        print("capture_max_view clicked")
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), "quick_viewport_capture.jpg")
        ms_path = temp_path.replace('\\', '/')
        print("图片保存路径：", temp_path)
        try:
            with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
                f.write('开始截图...\n')
            import pymxs
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
            print("截图代码已执行")
            with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
                f.write('截图代码已执行\n')
            print("文件是否存在：", os.path.exists(temp_path))
            with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f'文件是否存在：{os.path.exists(temp_path)}\n')
            # 图片加载
            print("开始加载图片...")
            pixmap = QtGui.QPixmap(temp_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.viewImageLabel.width(), self.viewImageLabel.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.viewImageLabel.setPixmap(scaled)
                self.viewImageLabel.setText("")
            else:
                self.viewImageLabel.setPixmap(QtGui.QPixmap())
                self.viewImageLabel.setText("未获取到视图")
            print("图片加载已执行")
            with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
                f.write('图片加载已执行\n')
        except Exception as e:
            print("捕获到异常：", e)
            with open(r'C:\Temp\max_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f'捕获到异常：{e}\n')

class MaxStylePanelQt(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MaxStylePanelQt, self).__init__(parent)
        self.setWindowTitle("多Tab演示面板（Qt版）")
        self.resize(600, 760)  # 初始高度调大
        self.setStyleSheet("background-color: #222;")
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(18)
        # 主Tab
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setStyleSheet("""
QTabBar::tab {
    min-width: 100px;
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
    padding: 6px 18px 6px 18px;
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
        tabNames = ["室内设计", "建筑规划", "景观设计", "图像处理"]
        for name in tabNames:
            tab = QtWidgets.QWidget()
            tabLayout = QtWidgets.QVBoxLayout(tab)
            tabLayout.setContentsMargins(0, 0, 0, 0)
            tabLayout.setSpacing(0)
            tabContent = TabContentWidget(name)
            tabLayout.addWidget(tabContent)
            tab.setLayout(tabLayout)
            self.tabWidget.addTab(tab, name)
        mainLayout.addWidget(self.tabWidget)
        self.setLayout(mainLayout)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        # 监听主窗口激活事件
        main_win = self.get_max_main_window()
        if main_win:
            main_win.installEventFilter(self)
        self.main_win = main_win

    def get_max_main_window(self):
        try:
            import MaxPlus
            import shiboken2
            main_win_ptr = MaxPlus.GetQMaxMainWindow()
            return shiboken2.wrapInstance(int(main_win_ptr), QtWidgets.QWidget)
        except Exception:
            return None

    def eventFilter(self, obj, event):
        if obj == self.main_win and event.type() == QtCore.QEvent.WindowActivate:
            self.show()
            self.raise_()
        return super(MaxStylePanelQt, self).eventFilter(obj, event)

if __name__ == '__main__':
    try:
        for w in QtWidgets.QApplication.allWidgets():
            if w.windowTitle() == u"多Tab演示面板（Qt版）":
                w.close()
    except:
        pass
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    # 获取3ds Max主窗口作为parent
    try:
        import MaxPlus
        import shiboken2
        def get_max_main_window():
            main_win_ptr = MaxPlus.GetQMaxMainWindow()
            return shiboken2.wrapInstance(int(main_win_ptr), QtWidgets.QWidget)
        parent = get_max_main_window()
    except Exception as e:
        parent = None
    win = MaxStylePanelQt(parent)
    # Dock嵌入方式
    try:
        import MaxPlus
        # 关闭同名Dock
        for dock in MaxPlus.Docking.GetDockableWindows():
            if dock[1] == "多Tab演示面板（Qt版）":
                MaxPlus.Docking.UnregisterDockableWindow(dock[0])
        MaxPlus.Docking.RegisterDockableWindow("多Tab演示面板（Qt版）", win, MaxPlus.Docking.DockLeft)
    except Exception as e:
        win.show() 