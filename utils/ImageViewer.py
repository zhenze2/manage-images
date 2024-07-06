import shutil
import math
from PyQt5.QtWidgets import  QMainWindow,  QVBoxLayout, QWidget, QPushButton, QMessageBox,   QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QCheckBox,QAction,QFileDialog,QDialog, QDialogButtonBox, QFormLayout,QDoubleSpinBox,QLabel,QGridLayout,QScrollArea,QSpinBox,QStatusBar,QApplication
from PyQt5.QtCore import Qt, QTimer, QEvent, QRectF
from PyQt5.QtGui import QPixmap,QKeyEvent
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
from netCDF4 import Dataset
import pandas as pd
import os
from utils.func import Config
import cv2
import numpy as np
import re

class ShowImage(QMainWindow):
    windows=[]
    def __init__(self,tree,time_entry):
        super().__init__()
        self.current_Node=None
        self.tree=tree
        self.playing=False
        self.timer_id=None
        self.time_entry=time_entry
        self.image_path = None
        self.image_name = None
        self.pixmap = None
        self.svg=None
        self.zoom_factor = 1.1
        self.re_current_local=False
        self.image_type = None
        self.get_circle=False
        self.initUI()
    def initUI(self):
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.viewport().installEventFilter(self)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.graphics_view)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 设置状态栏
        self.status_bar = QStatusBar()
        
        # 设置按钮
        button_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张")
        self.play_button = QPushButton("自动播放")
        self.local_button = QCheckBox("局部播放")
        self.next_button = QPushButton("下一张")
        self.prev_button.setFixedHeight(25)
        self.play_button.setFixedHeight(25)
        self.local_button.setFixedHeight(25)
        self.local_button.setChecked(False)        
        self.next_button.setFixedHeight(25)
        self.status_bar.setFixedWidth(250)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.local_button)
        button_layout.addWidget(self.status_bar)
        button_layout.addWidget(self.next_button)
        
        # 将按钮放置在布局底部
        main_layout.addLayout(button_layout)
        
        # 设置布局的边距
        main_layout.setContentsMargins(0,0,0,0)  # 左，上，右，下
        button_layout.setContentsMargins(0, 0, 0, 0)  # 使按钮紧靠窗口底部边缘

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.prev_button.clicked.connect(self.play_last_image)
        self.next_button.clicked.connect(self.play_next_image)
        self.play_button.clicked.connect(self.auto_play)
        self.local_button.clicked.connect(self.play_local)
        # 设置按钮长按绑定
        self.prev_button.setAutoRepeat(True)    # 长按的时候出发点击事件重复触发
        self.next_button.setAutoRepeat(True)
        
        
        # 添加菜单栏
        menubar=self.menuBar()
        # 创建帮助菜单
        help_menu = menubar.addMenu('快捷键')
        # 添加动作到帮助菜单
        help_action = QAction('查看', self)
        help_action.triggered.connect(self.showHelp)
        help_menu.addAction(help_action)
        
        export_menu = menubar.addMenu('导出')
        export_action_fig = QAction('导出图片', self)
        export_action_fig.triggered.connect(self.save_pixmap)
        export_menu.addAction(export_action_fig)
        export_action_nc = QAction('导出数据', self)
        export_action_nc.triggered.connect(self.save_nc)
        export_menu.addAction(export_action_nc)
        self.windows.append(self)
        
        self.setMouseTracking(True)

    def showHelp(self):
        help_text = """
        <h3>快捷键</h3>
        <p>空格：自动播放图片</p>
        <p>A：播放上一张图片(长按连续播放)</p>
        <p>D：播放下一张图片(长按连续播放)</p>
        """
        QMessageBox.information(self, '帮助', help_text)

    def show_image(self, image_path):
        self.image_path = image_path
        # print(self.image_path, os.path.basename(self.image_path))
        self.image_name=os.path.basename(self.image_path)
        if image_path.lower().endswith('.svg'):
            self.image_type = 'svg'
            self.show_svg(image_path)
        else:
            self.image_type = 'raster'
            self.show_raster_image(image_path)
        self.status_bar.showMessage(f"纬度: N{0:.2f}\u00B0  经度: {0:.2f}\u00B0")
        self.show()
        if self.get_circle:
            self.centerx,self.centery,self.radius=self.detect_circle()
        else:
            self.centerx,self.centery,self.radius=-1,-1,-1
        pattern = r'_\d{4}?'+'$'
        name=os.path.splitext(self.image_name)[0]
        if re.search(pattern, name):
            self.time_pic=True
        else:
            self.time_pic=False
    def show_svg(self, svg_path):
        # 创建 QGraphicsScene 和 QGraphicsSvgItem
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.svg = QSvgRenderer(svg_path)
        self.resize_svg()
    def resize_svg(self):
        svg_item = QGraphicsSvgItem(self.image_path)
        self.graphics_scene.clear()
        self.graphics_scene.addItem(svg_item)
        self.graphics_scene.setSceneRect(QRectF(self.svg.viewBoxF()))
        self.graphics_view.fitInView(svg_item, Qt.KeepAspectRatio)
        self.graphics_view.show()
        # print(self.graphics_view.geometry().width()/self.graphics_view.geometry().height(),self.svg.defaultSize().width()/self.svg.defaultSize().height())
    def show_raster_image(self, image_path):
        # 加载png等普通图片
        self.pixmap = QPixmap(image_path)
        self.graphics_scene.addPixmap(self.pixmap)
        self.graphics_view.setScene(self.graphics_scene)
        # 根据图片大小设置窗口大小
        # width = int(self.pixmap.width()*0.5)
        # height = int(self.pixmap.height()*0.5)
        # self.setGeometry(100, 100, width, height)
        # self.minimumSize = QSize(width, height)
        self.resize_image_label()

    def resize_image_label(self):
        pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.graphics_scene.clear()
        self.graphics_scene.addItem(pixmap_item)
        # 设置场景的矩形区域
        self.graphics_scene.setSceneRect(QRectF(self.pixmap.rect()))
        # 调整图像大小以适应视图窗口
        # self.graphics_view.setTransformationMode(Qt.SmoothTransformation)
        pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        # self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        self.graphics_view.fitInView(pixmap_item, Qt.KeepAspectRatio)
        self.graphics_view.show()

    def next(self,node):
        n_node=None
        parent = node.parent()
        if parent==None:
            root_count = self.tree.topLevelItemCount()
            # 遍历所有根节点
            for i in range(root_count):
                if node == self.tree.topLevelItem(i):
                    return self.tree.topLevelItem((i+1)%root_count)
        for i in range(parent.childCount()):
            if parent.child(i)==node:
                if i == parent.childCount()-1:
                    return None
                n_node=parent.child(i+1)
                break
        if n_node:
            return n_node
        else:
            return None
    def prev(self,node):
        p_node=None
        parent = node.parent()
        if parent==None:
            root_count = self.tree.topLevelItemCount()
            # 遍历所有根节点
            for i in range(root_count-1,-1,-1):
                if node == self.tree.topLevelItem(i):
                    return self.tree.topLevelItem((i-1)%root_count)
        for i in range(parent.childCount()-1,-1,-1):
            if parent.child(i)==node:
                if i==0:
                    return None
                p_node=parent.child(i-1)
                break
        if p_node:
            return p_node
        else:
            return None
    def get_child(self,node,index):
        if node.childCount()>index:
            return node.child(index)
        else:
            return None

    def play_local(self,state):
        # print(state)
        if state:
            self.re_current_local=True
        else:
            self.re_current_local=False

    def play_next_image(self):
        # 播放下一张图片逻辑
        next_node = self.next(self.current_Node)
        while next_node and next_node.data(0, Qt.UserRole)[0]!="photo":# 图片文件
            if next_node.data(0, Qt.UserRole)[0] == "file":# 最底层的文件，名称有关文件地址
                next_node = next_node.parent()
            elif next_node.data(0, Qt.UserRole)[0] == "category":
                # next_node=self.select_from_category(next_node)
                while next_node.data(0, Qt.UserRole)[0] =="category":
                    next_node = self.get_child(next_node,0)
                    if not next_node:
                        break
            else:
                break
        if not next_node:
            # 当前节点没有相邻节点，尝试查找父节点的相邻节点
            parent_node = self.current_Node.parent()
            while parent_node and parent_node.data(0, Qt.UserRole)[0]!="photo":
                next_node = self.next(parent_node)
                if next_node and next_node.data(0, Qt.UserRole)[0]=="photo":
                    break
                if next_node and next_node.data(0, Qt.UserRole)[0]=="category":
                    # next_node=self.select_from_category(next_node)
                    while next_node.data(0, Qt.UserRole)[0] =="category":
                        next_node = self.get_child(next_node,0)
                    break
                parent_node = parent_node.parent()
        def local_play():
            parent=self.current_Node.parent()
            count=parent.childCount()
            for i in range(count):
                if parent.child(i)==self.current_Node:
                    return parent.child((i+1)%count)
        if self.re_current_local:
            next_node=local_play()
        if next_node:
            # print(next_node.data(0, Qt.UserRole))
            file_path = next_node.data(0, Qt.UserRole)[1]
            self.current_Node=next_node
            self.show_image(file_path)

    def play_last_image(self):
        # 播放上一张图片逻辑
        prev_node = self.prev(self.current_Node)
        while prev_node and prev_node.data(0, Qt.UserRole)[0]!="photo":
            if prev_node.data(0, Qt.UserRole)[0] == "file":
                prev_node = prev_node.parent()
            elif prev_node.data(0, Qt.UserRole)[0] == "category":
                # prev_node=self.select_from_category(prev_node)
                while prev_node.data(0, Qt.UserRole)[0] =="category":
                    prev_node = self.get_child(prev_node,prev_node.childCount()-1)
                    if not prev_node:
                        break
            else:
                break

        if not prev_node:
            # 当前节点没有相邻节点，尝试查找父节点的相邻节点
            parent_node = self.current_Node.parent()
            # print(self.prev(parent_node).text(0))
            while parent_node and parent_node.data(0, Qt.UserRole)[0]!="photo":
                prev_node = self.prev(parent_node)
                if prev_node and prev_node.data(0, Qt.UserRole)[0]=="photo":
                    break
                if prev_node and prev_node.data(0, Qt.UserRole)[0]=="category":
                    # prev_node=self.select_from_category(prev_node)
                    while prev_node.data(0, Qt.UserRole)[0] =="category":
                        prev_node = self.get_child(prev_node,prev_node.childCount()-1)
                    break
                parent_node = parent_node.parent()
        def local_play():
            parent=self.current_Node.parent()
            count=parent.childCount()
            for i in range(count):
                if parent.child(i)==self.current_Node:
                    return parent.child((i-1)%count)
        if self.re_current_local:
            prev_node=local_play()
        if prev_node:
            # print(prev_node.data(0, Qt.UserRole))
            file_path = prev_node.data(0, Qt.UserRole)[1]
            self.current_Node=prev_node
            self.show_image(file_path)
            # print(file_path)

    def auto_play(self):
        # 自动播放图片
        if self.playing:
            # 如果已经在自动播放，停止自动播放
            self.playing = False
            self.play_button.setText("自动播放")
            if self.timer_id:
                self.killTimer(self.timer_id)  # 取消之前的定时器
        else:
            # 如果不在自动播放，开始自动播放
            self.playing = True
            self.play_button.setText("停止播放")
            self.time = float(self.time_entry.text())
            self.timer_id = self.startTimer(int(self.time * 1000))  # 启动定时器

    def save_pixmap(self):
        if self.pixmap:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog  # 避免使用本地对话框以便更好地与PyQt5集成
            out_path, selected_filter = QFileDialog.getSaveFileName(None, "保存图片", self.image_name, "JPEG 文件 (*.jpg);;PNG 文件 (*.png);;BMP 文件 (*.bmp)",options=options)
            format_str = "JPG"
            # 根据所选过滤器确定文件扩展名
            if "JPEG" in selected_filter:
                format_str = "JPG"
            elif "PNG" in selected_filter:
                format_str = "PNG"
            elif "BMP" in selected_filter:
                format_str = "BMP"
            if out_path:
                self.pixmap.save(out_path, format_str, quality=100)

    def save_nc(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # 避免使用本地对话框以便更好地与PyQt5集成
        target_dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录",options=options)
        img_dir=os.path.dirname(self.image_path)
        img_name=os.path.basename(self.image_path)
        name=os.path.splitext(img_name)[0]
        name=name.replace('_A','')
        name=name.replace('_B','')
        img_dir=img_dir.replace('_A','')
        img_dir=img_dir.replace('_B','')
        extensions = ['.nc','.csv','.dat']
        ext='.nc'
        source_file_path=os.path.join(img_dir.replace("images","data"),name+ext)
        # print(source_file_path)
        if os.path.exists(source_file_path):
            try:
                # 构造目标文件的完整路径
                target_file_path = os.path.join(target_dir_path, name+ext)
                # 复制文件到目标路径
                shutil.copy(source_file_path, target_file_path)
                # self.status_bar.showMessage(f"文件已成功导出到: {target_dir_path}", 5000)
            except Exception as e:
                pass
                self.status_bar.showMessage(f"导出文件失败: {str(e)}", 5000)


    def detect_circle(self):
        # 读取并缩小图片尺寸
        image = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        image = cv2.equalizeHist(image)
        resized_image = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)  # 缩小一半
        # 应用高斯模糊以减少噪点
        blurred = cv2.GaussianBlur(resized_image, (3, 3), 0)
        # 使用霍夫圆检测来找到图片中的圆
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, minDist=100, param1=50, param2=30, minRadius=50, maxRadius=0)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                # 获取圆心坐标和半径，并放大至原图尺寸
                center_x = int(i[0] * 2)
                center_y = int(i[1] * 2)
                radius = int(i[2] * 2)
                return center_x, center_y, radius
        return None, None, None
    def pixel_to_coords(self, x, y,edge_latitude=45):
        # 获取图像的中心
        if self.get_circle:
            center_x, center_y, radius = self.centerx,self.centery,self.radius
        else:
            center_x = self.graphics_scene.width() / 2
            center_y = self.graphics_scene.height() / 2
            radius = min(center_x, center_y)

        # 计算从中心到点 (x, y) 的距离（半径）
        dx = x - center_x
        dy = y - center_y
        r = math.sqrt(dx**2 + dy**2)
        # 计算角度
        theta = math.atan2(dy, dx)
        # 将 r 转换为纬度
        # 这里假设图像的边缘是 edge_latitude 纬度，中心是北极（90度纬度）
        if r > radius:
            return 0,0
        latitude_range = 90 - edge_latitude
        latitude = 90 - (r / radius) * latitude_range

        # 将 theta 转换为经度
        longitude = math.degrees(theta)
        if longitude!=-90:
            longitude = (longitude + 90)%180
        else:
            longitude = 180

        return latitude, longitude
    def eventFilter(self, obj, event):
        '''
        事件过滤器，处理鼠标滚轮事件和拖动事件，实现图片的放大缩小和拖动
        '''
        # import logging
        # logging.basicConfig(level=logging.DEBUG)
        if self.graphics_view:
            if obj == self.graphics_view.viewport():
                if event.type() == QEvent.Wheel:
                    # logging.debug("Wheel event detected")
                    # 获取鼠标在视图中的位置
                    mouse_pos_view = event.pos()
                    mouse_pos_scene = self.graphics_view.mapToScene(mouse_pos_view)
                    delta = event.angleDelta().y()
                    if delta > 0:
                        scale_factor = self.zoom_factor
                    else:
                        scale_factor = 1 / self.zoom_factor
                    # 设置放大缩小的锚点为鼠标位置
                    self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                    self.graphics_view.scale(scale_factor, scale_factor)
                    self.graphics_view.setTransformationAnchor(QGraphicsView.NoAnchor)
                    return True
                elif event.type() == QEvent.MouseMove:
                    # logging.debug("Mouse move event detected")
                    # 显示经纬度
                    if not self.time_pic:
                        scene_coords = self.graphics_view.mapToScene(event.pos())
                        x, y = scene_coords.x(), scene_coords.y()
                        latitude, longitude = self.pixel_to_coords(x, y)
                        msg=f"纬度: N{latitude:.2f}\u00B0  经度: E{longitude:.2f}\u00B0" if longitude>0 else f"纬度: N{latitude:.2f}\u00B0  经度: W{abs(longitude):.2f}\u00B0"
                        if longitude==0 or longitude==180:
                            msg=f"纬度: N{latitude:.2f}\u00B0  经度: {longitude:.2f}\u00B0"
                        self.status_bar.showMessage(msg)
                        
                    if event.buttons() & Qt.LeftButton:
                        # logging.debug("Mouse drag event detected")
                        # 处理鼠标拖动事件
                        delta = event.pos() - self.last_mouse_pos
                        self.last_mouse_pos = event.pos()
                        self.graphics_view.horizontalScrollBar().setValue(
                            self.graphics_view.horizontalScrollBar().value() - delta.x())
                        self.graphics_view.verticalScrollBar().setValue(
                            self.graphics_view.verticalScrollBar().value() - delta.y())
                    return True
                elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    # logging.debug("Mouse button press event detected")
                    # 处理鼠标左键按下事件进行拖动
                    self.last_mouse_pos = event.pos()
                    return True
                elif event.type() == QEvent.Enter:
                    # logging.debug("Mouse enter event detected")
                    # 处理鼠标进入事件以确保能够正确处理MouseMove事件
                    self.graphics_view.viewport().setMouseTracking(True)
                    return True
        return super().eventFilter(obj, event)
    def timerEvent(self, event):
        # 自动播放下一张图片
        self.play_next_image()

    def keyPressEvent(self, a0:QKeyEvent):
        # print(a0.key())
        # 重写键盘按下事件，实现键盘控制图片的播放
        if a0.key() == Qt.Key_A:
            self.play_last_image()
        elif a0.key() == Qt.Key_D:
            self.play_next_image()
        elif a0.key() == Qt.Key_Space:
            self.auto_play()
        elif a0.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(a0)
    def showEvent(self, event):
        super().showEvent(event)
        if self.image_type == 'raster':
            self.resize_image_label()
        elif self.image_type == 'svg':
            self.resize_svg()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_type == 'raster':
            self.resize_image_label()
        elif self.image_type == 'svg':
            self.resize_svg()

    def closeEvent(self, event):
        ShowImage.windows.remove(self)  # 从列表中移除当前窗口
        event.accept()
    @classmethod
    def close_all(cls):
        # 静态方法，关闭所有窗口
        for window in cls.windows:
            window.close()


class RangeInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # 创建两个 QDoubleSpinBox 控件用于经度范围
        self.longitude_start = QDoubleSpinBox()
        self.longitude_end = QDoubleSpinBox()
        self.longitude_start.setRange(-180.0, 180.0)
        self.longitude_start.setSingleStep(0.1)
        self.longitude_end.setRange(-180.0, 180.0)
        self.longitude_end.setSingleStep(0.1)
        
        longitude_layout = QHBoxLayout()
        self.longitude_start.setFixedWidth(100)
        self.longitude_end.setFixedWidth(100)
        longitude_layout.addWidget(QLabel("开始"))
        longitude_layout.addWidget(self.longitude_start)
        longitude_layout.addWidget(QLabel("结束"))
        longitude_layout.addWidget(self.longitude_end)

        # 创建两个 QDoubleSpinBox 控件用于纬度范围
        self.latitude_start = QDoubleSpinBox()
        self.latitude_end = QDoubleSpinBox()
        self.latitude_start.setRange(-90.0, 90.0)
        self.latitude_start.setSingleStep(0.1)
        self.latitude_end.setRange(-90.0, 90.0)
        self.latitude_end.setSingleStep(0.1)
        # 设置输入框宽度一致
        self.latitude_start.setFixedWidth(100)
        self.latitude_end.setFixedWidth(100)
        latitude_layout = QHBoxLayout()
        latitude_layout.addWidget(QLabel("开始"))
        latitude_layout.addWidget(self.latitude_start)
        latitude_layout.addWidget(QLabel("结束"))
        latitude_layout.addWidget(self.latitude_end)

        # 创建两个 QDoubleSpinBox 控件用于时间范围
        self.time_start = QDoubleSpinBox()
        self.time_end = QDoubleSpinBox()
        self.time_start.setRange(0.0, 24.0)  # 示例范围，可以根据需要调整
        self.time_start.setSingleStep(0.1)
        self.time_end.setRange(0.0, 24.0)
        self.time_end.setSingleStep(0.1)
        # 设置输入框宽度一致
        self.time_start.setFixedWidth(100)
        self.time_end.setFixedWidth(100)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("开始"))
        time_layout.addWidget(self.time_start)
        time_layout.addWidget(QLabel("结束"))
        time_layout.addWidget(self.time_end)

        # 将每个水平布局添加到表单布局
        form_layout.addRow("经度范围:", longitude_layout)
        form_layout.addRow("纬度范围:", latitude_layout)
        form_layout.addRow("时间范围:", time_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.longitude_start.valueChanged.connect(lambda: self.update_ac_value(self.longitude_start,self.longitude_end))
        self.latitude_start.valueChanged.connect(lambda: self.update_ac_value(self.latitude_start,self.latitude_end))
        self.time_start.valueChanged.connect(lambda: self.update_ac_value(self.time_start,self.time_end))
        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.setWindowTitle("选择范围")

    def update_ac_value(self,widget1,widget2):
        value=widget1.value()
        if widget2.value()<value:
            widget2.setValue(value)
    def get_values(self):
        longitude_start = self.longitude_start.value()
        longitude_end = self.longitude_end.value()
        latitude_start = self.latitude_start.value()
        latitude_end = self.latitude_end.value()
        time_start = self.time_start.value()
        time_end = self.time_end.value()
        return (longitude_start, longitude_end), (latitude_start, latitude_end), (time_start, time_end)
    

class MutiShowImage(ShowImage):
    def __init__(self, tree, time_entry,image_paths=None):
        self.current_Nodes = []
        self.tree = tree
        self.time_entry = time_entry
        self.image_paths = image_paths  # 存储图片路径列表
        self.image_names = []
        self.pixmaps = []
        self.svgs = []
        self.zoom_factor = 1.1
        self.re_current_local = False
        self.image_types = []
        self.image_checkboxes = []
        self.graphics_views = []  # 存储多个QGraphicsView
        self.graphics_scenes = []  # 存储多个QGraphicsScene
        self.check_names=[]
        self.graphics_view = None
        super().__init__(tree, time_entry)
        self.playing = [False] * len(self.image_paths)
        self.timers = [None] * len(self.image_paths)
    def initUI(self):
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()  # 使用网格布局
        row_count = int(len(self.image_paths)**0.5+0.5)
        for i in range(len(self.image_paths)):
            graphics_view = QGraphicsView()
            graphics_scene = QGraphicsScene()
            graphics_view.viewport().installEventFilter(self)
            graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            graphics_view.setFrameStyle(0)  # 去掉边框
            self.graphics_views.append(graphics_view)
            self.graphics_scenes.append(graphics_scene)

            row = i // row_count  # 行数
            col = i % row_count  # 列数
            grid_layout.addWidget(graphics_view, row, col)

        grid_layout.setContentsMargins(0, 0, 0, 0)
        # grid_layout.setSpacing(0)
        main_layout.addLayout(grid_layout)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 设置按钮
        button_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张")
        self.play_button = QPushButton("自动播放")
        # self.local_button = QCheckBox("局部播放")
        self.zoom_button = QCheckBox("整体放缩")
        self.next_button = QPushButton("下一张")
        self.prev_button.setFixedHeight(25)
        self.play_button.setFixedHeight(25)
        # self.local_button.setFixedHeight(25)
        self.zoom_button.setFixedHeight(25)
        # self.local_button.setChecked(False)
        self.zoom_button.setChecked(False)
        self.next_button.setFixedHeight(25)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        # button_layout.addWidget(self.local_button, alignment=Qt.AlignCenter)  # 设置复选框居中
        button_layout.addWidget(self.zoom_button, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.next_button)
        
        main_layout.addLayout(button_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 左，上，右，下
        button_layout.setContentsMargins(0, 0, 0, 0)  # 使按钮紧靠窗口底部边缘

        scroll_area = QScrollArea()
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_widget.setLayout(checkbox_layout)
        scroll_area.setWidget(checkbox_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(50)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout = checkbox_layout
        step_scroll=QHBoxLayout()
        # self.step=QDoubleSpinBox()
        self.step=QSpinBox()
        self.step.setRange(1,100)
        step_scroll.addWidget(QLabel("步长"))
        step_scroll.addWidget(self.step)
        step_scroll.addWidget(scroll_area)
        step_scroll.setAlignment(Qt.AlignCenter)
        step_scroll.setContentsMargins(0, 0, 0, 0)
        step_scroll_widget=QWidget()
        step_scroll_widget.setLayout(step_scroll)
        step_scroll_widget.setFixedHeight(50)
        main_layout.addWidget(step_scroll_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.installEventFilter(self)

        self.prev_button.clicked.connect(self.play_last_image)
        self.next_button.clicked.connect(self.play_next_image)
        self.play_button.clicked.connect(self.auto_play)
        # self.local_button.clicked.connect(self.play_local)
        self.zoom_button.clicked.connect(self.toggle_zoom_mode)
        self.prev_button.setAutoRepeat(True)
        self.next_button.setAutoRepeat(True)
        self.windows.append(self)
    def show_images(self, image_paths,index=None):
        if index is not None:
            # print("Show image in index:",index," with path:",image_paths,'and lenth of image_paths:',len(self.image_paths))
            self.image_paths[index] = image_paths
            self.image_names[index] = os.path.basename(image_paths)
            image_path=image_paths
            if image_path.lower().endswith('.svg'):
                self.image_types[index]='svg'
                self.show_svg(image_path, index)
            else:
                # print(image_path)
                self.image_types[index]='raster'
                self.show_raster_image(image_path, index)
        else:
            self.image_paths = image_paths
            self.image_names = [os.path.basename(path) for path in image_paths]
            for i, image_path in enumerate(image_paths):
                if image_path.lower().endswith('.svg'):
                    self.image_types.append('svg')
                    self.show_svg(image_path, i)
                else:
                    # print(image_path)
                    self.image_types.append('raster')
                    self.show_raster_image(image_path, i)
                checkbox = QCheckBox(self.check_names[i])
                checkbox.setChecked(True)
                self.checkbox_layout.addWidget(checkbox)
                self.image_checkboxes.append(checkbox)
        self.show()

    def show_svg(self, svg_path, index):
        self.graphics_scenes[index].clear()
        self.graphics_views[index].setScene(self.graphics_scenes[index])
        if index>=len(self.svgs):
            self.svgs.append(QSvgRenderer(svg_path))
        else:
            self.svgs[index]=QSvgRenderer(svg_path)
        svg_item = QGraphicsSvgItem(svg_path)
        self.graphics_scenes[index].addItem(svg_item)
        self.graphics_scenes[index].setSceneRect(QRectF(self.svgs[-1].viewBoxF()))
        self.graphics_views[index].fitInView(svg_item, Qt.KeepAspectRatio)
        self.graphics_views[index].show()

    def resize_svg(self):
        for i, svg in enumerate(self.svgs):
            svg_item = QGraphicsSvgItem()
            svg_item.setSharedRenderer(svg)
            self.graphics_scenes[i].clear()
            self.graphics_scenes[i].addItem(svg_item)
            self.graphics_views[i].setScene(self.graphics_scenes[i])
            self.graphics_scenes[i].setSceneRect(QRectF(svg.viewBoxF()))
            self.graphics_views[i].fitInView(svg_item, Qt.KeepAspectRatio)
            self.graphics_views[i].show()
    def show_raster_image(self, image_path, index):
        pixmap = QPixmap(image_path)
        if index >= len(self.pixmaps):
            self.pixmaps.append(pixmap)
        else:
            self.pixmaps[index] = pixmap
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.graphics_scenes[index].clear()
        self.graphics_scenes[index].addItem(pixmap_item)
        self.graphics_views[index].setScene(self.graphics_scenes[index])
        self.graphics_scenes[index].setSceneRect(QRectF(pixmap.rect()))
        pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.graphics_views[index].fitInView(pixmap_item, Qt.KeepAspectRatio)
        self.graphics_views[index].show()
        
    def resize_image_label(self):
        for i, pixmap in enumerate(self.pixmaps):
            pixmap_item = QGraphicsPixmapItem(pixmap)
            # self.graphics_scenes[i].clear()
            # self.graphics_scenes[i].addItem(pixmap_item)
            # self.graphics_views[i].setScene(self.graphics_scenes[i])
            self.graphics_scenes[i].setSceneRect(QRectF(pixmap.rect()))
            pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            self.graphics_views[i].fitInView(pixmap_item, Qt.KeepAspectRatio)
            self.graphics_views[i].show()

    def play_next_image(self):
        for i in range(len(self.current_Nodes)):
            if self.image_checkboxes[i].isChecked():
                self.show_next_image(i)

    def play_last_image(self):
        for i in range(len(self.current_Nodes)):
            if self.image_checkboxes[i].isChecked():
                self.show_last_image(i)
    def show_next_image(self, index):
        next_node=self.next(self.current_Nodes[index],int(self.step.value()))
        file_path = next_node.data(0, Qt.UserRole)[1]
        self.current_Nodes[index]=next_node
        self.show_images(file_path,index)

    def show_last_image(self, index):
        prev_node=self.prev(self.current_Nodes[index],int(self.step.value()))
        file_path = prev_node.data(0, Qt.UserRole)[1]
        self.current_Nodes[index]=prev_node
        self.show_images(file_path,index)
    def next(self, node, step=1):
        def get_siblings(node):
            parent = node.parent()
            if parent:
                return [parent.child(i) for i in range(parent.childCount())], 'child'
            else:
                return [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())], 'top'
        current_node = node
        remaining_step = step
        siblings,flag = get_siblings(current_node)
        idx = siblings.index(current_node)
        if flag=='top':
            # current_node is top level
            return siblings[(idx + remaining_step) % len(siblings)]
        if idx + remaining_step < len(siblings):
            return siblings[idx + remaining_step]
        else:
            remaining_step = remaining_step+idx-len(siblings)
            level=1
            parent=current_node.parent()
            while level>0:
                p_siblings,flag=get_siblings(parent)
                p_idx=p_siblings.index(parent)
                # print(level,parent.text(0) if parent else None,p_idx,len(p_siblings))
                if p_idx+1<len(p_siblings):
                    parent=p_siblings[p_idx+1]
                    if parent.childCount()==0:
                        continue
                    current_node=p_siblings[p_idx+1].child(0)
                    parent=current_node
                    level-=1
                    n=0
                    while n<level:
                        p_siblings,_=get_siblings(current_node)
                        current_node=p_siblings[0].child(0)
                        n+=1
                        if current_node is None:
                            n=0
                            break
                    level-=n
                elif flag=='top':
                    current_node=p_siblings[(p_idx+1)%len(p_siblings)].child(0)
                    level-=1
                    n=0
                    while n<level:
                        if current_node.childCount()==0:
                            parent=current_node
                            break
                        p_siblings,_=get_siblings(current_node)
                        current_node=p_siblings[0].child(0)
                        n+=1
                    level-=n
                else:
                    parent=parent.parent()
                    level+=1
            return self.next(current_node,remaining_step)
    def prev(self, node, step=1):
        def get_siblings(node):
            parent = node.parent()
            if parent:
                return [parent.child(i) for i in range(parent.childCount()-1,-1,-1)], 'child'
            else:
                return [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount()-1,-1,-1)], 'top'
        current_node = node
        remaining_step = step
        siblings,flag = get_siblings(current_node)
        idx = siblings.index(current_node)
        if flag=='top':
            # current_node is top level
            return siblings[(idx + remaining_step) % len(siblings)]
        if idx + remaining_step < len(siblings):
            return siblings[idx + remaining_step]
        else:
            remaining_step = remaining_step+idx-len(siblings)
            level=1
            parent=current_node.parent()
            while level>0:
                p_siblings,flag=get_siblings(parent)
                p_idx=p_siblings.index(parent)
                # print(level,parent.text(0) if parent else None,p_idx,len(p_siblings))
                if p_idx+1<len(p_siblings):
                    parent=p_siblings[p_idx+1]
                    if parent.childCount()==0:
                        continue
                    current_node=p_siblings[p_idx+1]
                    current_node=current_node.child(current_node.childCount()-1)
                    parent=current_node
                    level-=1
                    n=0
                    while n<level:
                        p_siblings,_=get_siblings(current_node)
                        current_node=p_siblings[0]
                        current_node=current_node.child(current_node.childCount()-1)
                        n+=1
                        if current_node is None:
                            n=0
                            break
                    level-=n
                elif flag=='top':
                    current_node=p_siblings[(p_idx+1)%len(p_siblings)]
                    current_node=current_node.child(current_node.childCount()-1)
                    level-=1
                    n=0
                    while n<level:
                        if current_node.childCount()==0:
                            parent=current_node
                            break
                        p_siblings,_=get_siblings(current_node)
                        current_node=p_siblings[0]
                        current_node=current_node.child(current_node.childCount()-1)
                        n+=1
                    level-=n
                else:
                    parent=parent.parent()
                    level+=1
            return self.prev(current_node,remaining_step)
    def auto_play(self):
        l=len(self.current_Nodes)
        if True in self.playing:  # Assuming we control all views together
            for i in range(l):
                self.playing[i] = False
                if self.timers[i]:
                    self.timers[i].stop()
            self.play_button.setText("自动播放")
        else:
            for i in range(l):
                if not self.image_checkboxes[i].isChecked():
                    continue
                self.playing[i] = True
                self.timers[i] = QTimer(self)
                self.timers[i].timeout.connect(lambda i=i: self.show_next_image(i))
                self.timers[i].start(int(float(self.time_entry.text()) * 1000))
            self.play_button.setText("停止播放")

    def timerEvent(self, event):
        self.play_next_image()

    def eventFilter(self, source, event):
        if self.zoom_button.isChecked():
            if event.type() == QEvent.Wheel:
                delta = event.angleDelta().y()
                scale_factor = self.zoom_factor if delta > 0 else 1 / self.zoom_factor
                # 同步更新所有视图的缩放级别
                for view in self.graphics_views:
                    view.scale(scale_factor, scale_factor)
                return True  # 事件被处理
        else:
            for graphics_view in self.graphics_views:
                if source == graphics_view.viewport() and event.type() == QEvent.Wheel:
                    # 获取鼠标在视图中的位置
                    mouse_pos_view = event.pos()
                    mouse_pos_scene = graphics_view.mapToScene(mouse_pos_view)
                    delta = event.angleDelta().y()
                    if delta > 0:
                        scale_factor = self.zoom_factor
                    else:
                        scale_factor = 1 / self.zoom_factor
                    # 设置放大缩小的锚点为鼠标位置
                    graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                    graphics_view.scale(scale_factor, scale_factor)
                    graphics_view.setTransformationAnchor(QGraphicsView.NoAnchor)
                    return True
                elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and source == graphics_view.viewport():
                    # 处理鼠标左键按下事件进行拖动
                    self.last_mouse_pos = event.pos()
                    return True
                elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton and source == graphics_view.viewport():
                    # 处理鼠标拖动事件
                    delta = event.pos() - self.last_mouse_pos
                    self.last_mouse_pos = event.pos()
                    graphics_view.horizontalScrollBar().setValue(
                        graphics_view.horizontalScrollBar().value() - delta.x())
                    graphics_view.verticalScrollBar().setValue(
                        graphics_view.verticalScrollBar().value() - delta.y())
                    return True
        return super().eventFilter(source, event)
    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_A:
                self.play_last_image()
            elif event.key() == Qt.Key_D:
                self.play_next_image()
            elif event.key() == Qt.Key_Space:
                self.auto_play()
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_types[0] == 'raster':
            self.resize_image_label()
        elif self.image_types[0] == 'svg':
            self.resize_svg()
    def showEvent(self, event):
        super().showEvent(event)
        if self.image_types[0] == 'raster':
            self.resize_image_label()
        elif self.image_types[0] == 'svg':
            self.resize_svg()
    def toggle_zoom_mode(self):
        if self.zoom_button.isChecked():
            self.zoom_factor = 1.1
        else:
            self.zoom_factor = 1.1

if __name__ == "__main__":
    "测试保存"
    from PyQt5.QtWidgets import QApplication, QFileDialog, QTreeWidget
    import sys
    from func import update_treeview,load_index_image,find_node_by_path
    import time
    app = QApplication(sys.argv)
    images=[r'D:\source_python\Index_search\images00\1-1.png']*3
    images=[r'D:\source_python\Index_search\images00\1-1.svg']*16
    # images,_=QFileDialog.getOpenFileNames(None, "Open file", 'c:\\', 'Image files(*.jpg *.gif *.png *.jpeg *.svg)')
    # print(images)
    # ShowImage(None,None).show_image(image_path=images[0])
    # MultiImageDisplay().show_images(images)
    
    # tree = QTreeWidget(None)
    # images_dic=load_index_image(r'D:\source_python\Index_search\conf\index_image.pkl')
    # update_treeview(tree, tree, images_dic)
    # start_time = time.perf_counter()
    # path=['SIA', '空间分布图', 'A', '2010', '12', '31.png']
    # path=['SID', '空间分布图', 'A', '2010', '12', '31.png']
    # item=find_node_by_path(tree,path)
    # print(images_dic.keys())
    # end_time = time.perf_counter()
    # print(item.data(0, Qt.UserRole) if item else None)
    # execution_time = end_time - start_time
    # print(f"函数执行时间: {execution_time} 秒")
    Ms=MutiShowImage(None,None,images)
    Ms.check_names=['12345678']*16
    Ms.show_images(images)
    sys.exit(app.exec_())

#函数执行时间: 5.649999999945976e-05 秒，字典搜索
#函数执行时间: 0.000823500000000088 秒，树搜索, 树搜索比字典搜索慢了14倍,但是树搜索更加直观，且时间仍然很短
# ['SIC', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIT-app-x-040', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIT-app-x-140', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIT-cs2smos', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIT-PIOMAS', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIE', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIV', '空间分布图', 'A', '2010', '12', '31.png']
# ['SID', '空间分布图', 'A', '2010', '12', '31.png']
# ['SIA', '空间分布图', 'A', '2010', '12', '31.png']