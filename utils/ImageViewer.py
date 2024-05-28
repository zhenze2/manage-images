from math import ceil

from PyQt5.QtWidgets import  QMainWindow,  QVBoxLayout, QWidget, QPushButton, QMessageBox,   QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QCheckBox,QAction
from PyQt5.QtCore import Qt,  QEvent, QRectF
from PyQt5.QtGui import QPixmap,QKeyEvent
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem


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
        self.pixmap = None
        self.svg=None
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        self.zoom_factor = 1.1
        
        self.re_current_local=False
        self.image_type = None

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
            # print(file_path)

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
