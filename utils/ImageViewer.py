from math import ceil

from PyQt5.QtWidgets import  QMainWindow,  QVBoxLayout, QWidget, QPushButton, QMessageBox,   QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QCheckBox,QAction,QFileDialog,QDialog, QDialogButtonBox, QFormLayout,QDoubleSpinBox,QLabel,QGridLayout
from PyQt5.QtCore import Qt, QTimer, QEvent, QRectF
from PyQt5.QtGui import QPixmap,QKeyEvent
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
from netCDF4 import Dataset
import pandas as pd
import os
# from utils.func import Config

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
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.local_button, alignment=Qt.AlignCenter)  # 设置复选框居中
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
        self.show()
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
            out_path, selected_filter = QFileDialog.getSaveFileName(None, "Save Image", self.image_name, "JPEG 文件 (*.jpg);;PNG 文件 (*.png);;BMP 文件 (*.bmp)")
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
        # 读取CSV文件
        path = os.path.join(Config.current_dir,"1.xlsx")
        data = pd.read_excel(path)
        dialog=RangeInputDialog()
        dialog.show()
        longitude_scale, latitude_scale, time_scale=(0,0),(0,0),(0,0)
        if dialog.exec() == QDialog.Accepted:
            longitude_scale, latitude_scale, time_scale = dialog.get_values()
        elif dialog.exec() == QDialog.Rejected:
            return
        nc_name=f'{time_scale}_{latitude_scale}_{longitude_scale}.nc'
        nc_file,_ = QFileDialog.getSaveFileName(None, "Save Nc File", nc_name, "NETCDF4 文件 (*.nc)")
        # 创建NetCDF文件
        if nc_file:
            with Dataset(nc_file, 'w', format='NETCDF4') as nc:
                # 定义维度，例如时间（time）和空间（space）
                time_dim = nc.createDimension('time', len(data['time_column']))  # 替换'time_column'为你的实际时间列名
                space_dim = nc.createDimension('space', len(data['space_column']))  # 替换'space_column'为你的实际空间列名

                # 创建变量
                time_var = nc.createVariable('time', 'f8', ('time',))  # 时间变量
                space_var = nc.createVariable('space', 'i4', ('space',))  # 空间变量
                data_var = nc.createVariable('data_variable', 'f8', ('time', 'space'))  # 你的数据变量

                # 将数据填充到变量中
                time_var[:] = data['time_column'].values  # 用实际时间数据填充
                space_var[:] = data['space_column'].values  # 用实际空间数据填充
                data_var[:] = data['your_data_column'].values.reshape(-1, len(data['space_column']))  # 用你的数据填充，确保数据形状正确

                # 设置变量属性
                time_var.long_name = 'Time'  # 变量描述
                time_var.units = 'seconds since 1970-01-01 00:00:00'  # 单位
                space_var.long_name = 'Space'  # 变量描述
                data_var.long_name = 'Your Data Description'  # 数据描述
                data_var.units = 'Your Data Units'  # 数据单位

    def eventFilter(self, obj, event):
        '''
        事件过滤器，处理鼠标滚轮事件和拖动事件，实现图片的放大缩小和拖动
        '''
        if self.graphics_view:
            if obj == self.graphics_view.viewport() and event.type() == QEvent.Wheel:
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
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # 处理鼠标左键按下事件进行拖动
                self.last_mouse_pos = event.pos()
                return True
            elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
                # 处理鼠标拖动事件
                delta = event.pos() - self.last_mouse_pos
                self.last_mouse_pos = event.pos()
                self.graphics_view.horizontalScrollBar().setValue(
                    self.graphics_view.horizontalScrollBar().value() - delta.x())
                self.graphics_view.verticalScrollBar().setValue(
                    self.graphics_view.verticalScrollBar().value() - delta.y())
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


class MultiImageDisplay(ShowImage):
    def __init__(self):
        super().__init__(None,None)
        self.setWindowTitle("Multi Image Viewer")
        self.image_widget=QWidget()
        self.zoom_factor = 1.1
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        
        # 添加一个按钮，用于显示新的图片
        # add_image_button = QPushButton("Add Image")
        # add_image_button.clicked.connect(self.add_image_widget)
        # self.main_layout.addWidget(add_image_button)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # 创建一个 QGraphicsView 和 QGraphicsScene 用于显示图片
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        layout.addWidget(self.graphics_view)
        self.image_widget.setLayout(layout)
        self.main_layout.addWidget(self.image_widget)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
        
        self.graphics_view.viewport().installEventFilter(self)

    def add_image_widget(self):
        # 创建一个新的图片显示组件，并添加到窗口中
        # image_widget = ImageWidget()
        # self.image_layout.addWidget(image_widget)
        # self.image_widgets.append(image_widget)
        # image_paths = QFileDialog.getOpenFileNames(self, 'Open file', 'c:\\', 'Image files(*.jpg *.gif *.png *.jpeg *.svg)')
        # 显示消息框
    # def show_images(self, image_paths):
    #     # 直接显示给定的多张图片
    #     for index, image_path in enumerate(image_paths):
    #         if index < len(self.image_widgets):
    #             self.image_widgets[index].show_image(image_path)
    #         else:
    #             image_widget = ImageWidget()
    #             self.image_layout.addWidget(image_widget)
    #             image_widget.show_image(image_path)
    #             # image_widget.setContentsMargins(0, 0, 0, 0)
    #             self.image_widgets.append(image_widget)
        QMessageBox.information(self, '消息', '新增')

    def show_images(self, image_path):
        # 直接显示给定的多张相同格式图片
        self.image_path = image_path
        if len(image_path)==0:
            QMessageBox.information(self, '消息', '未找到图片')
            return
        if image_path[0].lower().endswith('.svg'):
            self.image_type = 'svg'
            self.show_svg(image_path)
        else:
            self.image_type = 'raster'
            self.show_raster_image(image_path)
        self.show()
        self.image_widget.show()

    def show_svg(self, svg_path):
        # 加载svg图片
        self.svgs=[]
        for path in svg_path:
            self.svgs.append(path)
        self.graphics_view.setScene(self.graphics_scene)
        self.resize_svg()
    def resize_svg(self):
        self.graphics_scene.clear()
        width = 0
        height = 0
        n=len(self.svgs)
        num_images_per_row = self.optimal_images_per_row(n,QSvgRenderer(self.svgs[0]).viewBox().width(),QSvgRenderer(self.svgs[0]).viewBox().height(),self.geometry().width()/self.geometry().height())
        max_width = 0
        max_height = 0
        for i in range(n):
            svg=QSvgRenderer(self.svgs[i])
            if i % num_images_per_row == 0:
                width = 0
                height += svg.viewBoxF().height()
            max_height = max(max_height, height)
            
            svg_item = QGraphicsSvgItem(self.svgs[i])
            svg_item.setPos(width, height-svg.viewBoxF().height())
            self.graphics_scene.addItem(svg_item)
            
            width += svg.viewBoxF().width()
            max_width = max(max_width, width)
        self.graphics_scene.setSceneRect(QRectF(0,0,max_width,max_height))
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        self.graphics_view.show()
    def show_raster_image(self, image_path):
        # 加载png等普通图片
        self.pixmaps=[]
        for path in image_path:
            self.pixmaps.append(QPixmap(path))
        self.graphics_view.setScene(self.graphics_scene)
        # 统一所有图片的大小
        max_width = min([pixmap.width() for pixmap in self.pixmaps])
        max_height = min([pixmap.height() for pixmap in self.pixmaps])
        for i in range(len(self.pixmaps)):
            self.pixmaps[i] = self.pixmaps[i].scaled(max_width, max_height)
        self.resize_image_label()

    def resize_image_label(self):
        self.graphics_scene.clear()
        width = 0
        height = 0
        n=len(self.pixmaps)
        num_images_per_row = self.optimal_images_per_row(n,self.pixmaps[0].width(),self.pixmaps[0].height(),ratio=self.geometry().width()/self.geometry().height())
        max_width = 0
        max_height = 0
        for i in range(n):
            pixmap =self.pixmaps[i]
            if i % num_images_per_row == 0:
                width = 0
                height += pixmap.height()
            max_height = max(max_height, height)
            
            pixmap_item = QGraphicsPixmapItem(pixmap)
            pixmap_item.setPos(width, height-pixmap.height())
            pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            self.graphics_scene.addItem(pixmap_item)
            
            width += pixmap.width()
            max_width = max(max_width, width)
        self.graphics_scene.setSceneRect(QRectF(0,0,max_width,max_height))
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        self.graphics_view.show()

    def eventFilter(self, obj, event):
        '''
        事件过滤器，处理鼠标滚轮事件和拖动事件，实现图片的放大缩小和拖动
        '''
        if obj == self.graphics_view.viewport() and event.type() == QEvent.Wheel:
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
        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # 处理鼠标左键按下事件进行拖动
            self.last_mouse_pos = event.pos()
            return True
        elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
            # 处理鼠标拖动事件
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.graphics_view.horizontalScrollBar().setValue(
                self.graphics_view.horizontalScrollBar().value() - delta.x())
            self.graphics_view.verticalScrollBar().setValue(
                self.graphics_view.verticalScrollBar().value() - delta.y())
            return True
        return super().eventFilter(obj, event)


    def showEvent(self, event):
        super().showEvent(event)
        if self.image_type == 'raster':
            self.resize_image_label()
        elif self.image_type == 'svg':
            self.resize_svg()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # print(self.geometry().width(),self.geometry().height())
        if self.image_type == 'raster':
            self.resize_image_label()
        elif self.image_type == 'svg':
            self.resize_svg()
    
    @staticmethod
    def optimal_images_per_row(n,width=100,height=100,ratio=800/600):
        # Find the square root of the number of images to get an initial estimate
        sqrt_n = int(n ** 0.5)
        if sqrt_n == n**2:
            return sqrt_n
        num1 = sqrt_n
        num2 = sqrt_n+1
        
        num1_ratio = (num1*width)/(height*ceil(n/num1))
        num2_ratio = (num2*width)/(height*ceil(n/num2))
        if abs(num1_ratio-ratio) < abs(num2_ratio-ratio):
            return num1
        else:
            return num2



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
    def __init__(self, tree, time_entry):
        self.current_Nodes = []
        self.tree = tree
        self.time_entry = time_entry
        self.image_paths = []  # 存储图片路径列表
        self.image_names = []
        self.pixmaps = []
        self.svgs = []
        self.zoom_factor = 1.1
        self.re_current_local = False
        self.image_types = []
        self.graphics_views = []  # 存储多个QGraphicsView
        self.graphics_scenes = []  # 存储多个QGraphicsScene
        self.graphics_view = None
        super().__init__(tree, time_entry)
        self.playing = [False] * 4
        self.timers = [None] * 4
    def initUI(self):
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()  # 使用网格布局
        
        # 添加多个QGraphicsView到网格布局
        for i in range(2):
            for j in range(2):
                graphics_view = QGraphicsView()
                graphics_scene = QGraphicsScene()
                graphics_view.viewport().installEventFilter(self)
                graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                graphics_view.setFrameStyle(0)  # 去掉边框
                self.graphics_views.append(graphics_view)
                self.graphics_scenes.append(graphics_scene)
                grid_layout.addWidget(graphics_view, i, j)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        # grid_layout.setSpacing(0)
        main_layout.addLayout(grid_layout)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 设置按钮
        button_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张")
        self.play_button = QPushButton("自动播放")
        self.local_button = QCheckBox("局部播放")
        self.zoom_button = QCheckBox("整体放缩")
        self.next_button = QPushButton("下一张")
        self.prev_button.setFixedHeight(25)
        self.play_button.setFixedHeight(25)
        self.local_button.setFixedHeight(25)
        self.zoom_button.setFixedHeight(25)
        self.local_button.setChecked(False)
        self.zoom_button.setChecked(False)
        self.next_button.setFixedHeight(25)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.local_button, alignment=Qt.AlignCenter)  # 设置复选框居中
        button_layout.addWidget(self.zoom_button, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.next_button)
        
        main_layout.addLayout(button_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 左，上，右，下
        button_layout.setContentsMargins(0, 0, 0, 0)  # 使按钮紧靠窗口底部边缘

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.prev_button.clicked.connect(self.play_last_image)
        self.next_button.clicked.connect(self.play_next_image)
        self.play_button.clicked.connect(self.auto_play)
        self.local_button.clicked.connect(self.play_local)
        self.zoom_button.clicked.connect(self.toggle_zoom_mode)
        self.prev_button.setAutoRepeat(True)
        self.next_button.setAutoRepeat(True)
        
        # 添加菜单栏
        # menubar = self.menuBar()
        # help_menu = menubar.addMenu('快捷键')
        # help_action = QAction('查看', self)
        # help_action.triggered.connect(self.showHelp)
        # help_menu.addAction(help_action)
        
        # export_menu = menubar.addMenu('导出')
        # export_action_fig = QAction('导出图片', self)
        # export_action_fig.triggered.connect(self.save_pixmap)
        # export_menu.addAction(export_action_fig)
        # export_action_nc = QAction('导出数据', self)
        # export_action_nc.triggered.connect(self.save_nc)
        # export_menu.addAction(export_action_nc)
        self.windows.append(self)

    def show_images(self, image_paths,index=None):
        if index:
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
            self.show_next_image(i)

    def play_last_image(self):
        for i in range(len(self.current_Nodes)):
            self.show_last_image(i)
    def show_next_image(self, index):
        # 播放下一张图片逻辑
        next_node = self.next(self.current_Nodes[index])
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
            parent_node = self.current_Nodes[index].parent()
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
            parent=self.current_Nodes[index].parent()
            count=parent.childCount()
            for i in range(count):
                if parent.child(i)==self.current_Nodes[index]:
                    return parent.child((i+1)%count)
        if self.re_current_local:
            next_node=local_play()
        if next_node:
            file_path = next_node.data(0, Qt.UserRole)[1]
            print(file_path)
            self.current_Nodes[index]=next_node
            self.show_images(file_path,index)

    def show_last_image(self, index):
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
            self.show_images(file_path,index)

    def auto_play(self):
        if self.playing[0]:  # Assuming we control all views together
            for i in range(4):
                self.playing[i] = False
                if self.timers[i]:
                    self.timers[i].stop()
            self.play_button.setText("自动播放")
        else:
            for i in range(4):
                self.playing[i] = True
                self.timers[i] = QTimer(self)
                self.timers[i].timeout.connect(lambda i=i: self.show_next_image(i))
                self.timers[i].start(int(float(self.time_entry.text()) * 1000))
            self.play_button.setText("停止播放")

    def save_pixmap(self):
        for i, pixmap in enumerate(self.pixmaps):
            if pixmap:
                out_path, selected_filter = QFileDialog.getSaveFileName(
                    None, f"Save Image {i+1}", self.image_names[i], 
                    "JPEG 文件 (*.jpg);;PNG 文件 (*.png);;BMP 文件 (*.bmp)"
                )
                format_str = "JPG"
                if "JPEG" in selected_filter:
                    format_str = "JPG"
                elif "PNG" in selected_filter:
                    format_str = "PNG"
                elif "BMP" in selected_filter:
                    format_str = "BMP"
                if out_path:
                    pixmap.save(out_path, format_str, quality=100)

    def save_nc(self):
        path = os.path.join(Config.current_dir, "1.xlsx")
        data = pd.read_excel(path)
        dialog = RangeInputDialog()
        dialog.show()
        longitude_scale, latitude_scale, time_scale = (0, 0), (0, 0), (0, 0)
        if dialog.exec() == QDialog.Accepted:
            longitude_scale, latitude_scale, time_scale = dialog.get_values()

        nc_file_path, selected_filter = QFileDialog.getSaveFileName(
            None, "保存文件", "data.nc", "NetCDF files (*.nc)"
        )
        if nc_file_path:
            with Dataset(nc_file_path, 'w', format='NETCDF4') as ncfile:
                time_dim = ncfile.createDimension('time', len(data))
                space_dim = ncfile.createDimension('space', len(data.columns))

                time_var = ncfile.createVariable('time', 'f4', ('time',))
                space_var = ncfile.createVariable('space', 'f4', ('space',))
                data_var = ncfile.createVariable('data_variable', 'f4', ('time', 'space'))

                time_var[:] = data['time_column'].values
                space_var[:] = data['space_column'].values
                data_var[:, :] = data['data_variable'].values

                time_var.units = 'seconds since 2023-05-01 00:00:00'
                space_var.units = 'meters'
                data_var.units = 'unknown'

    def timerEvent(self, event):
        self.play_next_image()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Wheel and self.zoom_button.isChecked():
            delta = event.angleDelta().y()
            if delta > 0:
                scale_factor = 1 / self.zoom_factor
            else:
                scale_factor = self.zoom_factor
            # 同步更新所有视图的缩放级别
            for view in self.graphics_views:
                view.scale(scale_factor, scale_factor)
            return True  # 事件被处理
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
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # 处理鼠标左键按下事件进行拖动
                self.last_mouse_pos = event.pos()
                return True
            elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
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
        elif self.image_type == 'svg':
            self.resize_svg()
    def showEvent(self, event):
        super().showEvent(event)
        if self.image_types[0] == 'raster':
            self.resize_image_label()
        elif self.image_type == 'svg':
            self.resize_svg()
    def toggle_zoom_mode(self):
        if self.zoom_button.isChecked():
            self.zoom_factor = 1.1
        else:
            self.zoom_factor = 1.5

if __name__ == "__main__":
    "测试保存"
    from PyQt5.QtWidgets import QApplication, QFileDialog, QTreeWidget
    import sys
    from func import update_treeview,load_index_image,find_node_by_path
    import time
    app = QApplication(sys.argv)
    images=[r'D:\source_python\Index_search\images00\1-1.png']*4
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
    MutiShowImage(None,None).show_images(images)
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