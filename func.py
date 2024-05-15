import json
from math import ceil
import pickle
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QFileSystemModel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel,QListWidget,   QHBoxLayout, QGridLayout, QSplitter, QSizePolicy,QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QComboBox,QCheckBox,QScrollArea,QLayout
from PyQt5.QtCore import Qt, QTimer, QEvent,QRect, QRectF, QSize
from PyQt5.QtGui import QPixmap,QImage,QPainter
from PyQt5.QtSvg import QSvgWidget,QSvgRenderer, QGraphicsSvgItem

import sys
import copy
import os
import re

# 初始文件格式
DEFAULT_IMAGE_FORMAT = ".png" #[".jpg", ".jpeg", ".png"]
# 默认分隔符
SEPARATOR = "_"
# 主文件所在目录
CURRENT_DIR=None

def update_dir(current_dir):
    global CURRENT_DIR
    CURRENT_DIR=current_dir

def chinese_to_arabic_sort(arr):
    chinese_numbers= {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": "","百": "","千": "","万": "","亿": ""}
    arrb=copy.deepcopy(arr)
    for l in range(len(arrb)):
        chinese_num = re.findall(r'[一二三四五六七八九十百千万亿]+', arrb[l])
        for i in chinese_num:
            for j in i:
                if j=="十"  and i[0]==j:
                    if i[-1]==j:
                        arrb[l] = arrb[l].replace(j, "10")
                    else:
                        arrb[l] = arrb[l].replace(j, "1")
                elif j=="十" and i[-1]==j:
                    arrb[l] = arrb[l].replace(j, "0")
                elif j=="百" and i[-1]==j:
                    arrb[l] = arrb[l].replace(j, "00")
                elif j=="千" and i[-1]==j:
                    arrb[l] = arrb[l].replace(j, "000")
                elif j=="万" and i[-1]==j:
                    arrb[l] = arrb[l].replace(j, "0000")
                elif j=="亿" and i[-1]==j:
                    arrb[l] = arrb[l].replace(j, "00000000")
                else:
                    arrb[l] = arrb[l].replace(j, str(chinese_numbers[j]))
        sorted_b = [x for _, x in sorted(zip(arrb, arr), key=lambda x:int(re.findall(r'\d+',x[0])[0]) if len(re.findall(r'\d+',x[0]))>0  else 999999999999)]
    return sorted_b
def index_image_files(directory, image_format):
    index = {}  # 初始化索引字典
    for root, dirs, files in os.walk(directory):
        files = chinese_to_arabic_sort(files)
        for file in files:
            if file.endswith(image_format):
                if SEPARATOR not in file:
                    # QMessageBox.information(None, "错误",str(file)+ "不符合规范格式: 类别1"+SEPARATOR+"类别2"+SEPARATOR+"..."+SEPARATOR+"类别n"+SEPARATOR+"图片名称\n例如: cat"+SEPARATOR+"dog"+SEPARATOR+"1" + DEFAULT_IMAGE_FORMAT)
                    continue
                categories, filename = file.rsplit(SEPARATOR, maxsplit=1)
                categories = categories.strip().split(SEPARATOR)
                filename = filename.strip()

                curr_index = index  
                for category in categories:
                    curr_index = curr_index.setdefault(category, {})

                curr_index[filename] = os.path.join(root, file)
    if index == {}:
        QMessageBox.information(None, "错误", "未找到规范格式的图片文件")
    save_index_image(index)
    return index

def save_index_image(index_image):
    filename = os.path.join(CURRENT_DIR, "index_image.pkl")
    with open(filename, 'wb') as f:
        pickle.dump(index_image, f)

def load_index_image(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None
def update_category_tree(tree, directory_to_index):
    if not directory_to_index:
        return
    # 清空原有树视图
    tree.clear()
    category_index = index_image_files(directory_to_index, DEFAULT_IMAGE_FORMAT)
    update_treeview(tree, tree, category_index)

def browse_directory(entry_path,tree,image_path=None):
    """
    打开一个对话框，选择包含图像文件的目录。
    """
    if image_path:
        directory_path=image_path
        if entry_path:
            entry_path.setText(directory_path)
        update_category_tree(tree,directory_path)
    else:
        directory_path = QFileDialog.getExistingDirectory()
        if directory_path:
            entry_path.setText(directory_path)
            update_category_tree(tree,directory_path)

def update_treeview(tree, parent, categories):
    """
    递归地使用类别更新树视图。
    """
    if not categories:
        return
    for category, subcategories in categories.items():
        f_path = None
        NodeType = "category"
        if DEFAULT_IMAGE_FORMAT in category:
            f_path = categories[category]
            NodeType = "photo"
        item = QTreeWidgetItem(parent)
        item.setText(0, category)
        item.setData(0,Qt.UserRole,[NodeType,f_path])
        if isinstance(subcategories, dict):
            update_treeview(tree, item, subcategories)
        else:
            if type(subcategories) is str:
                f_path = subcategories
                NodeType = "file"
                child_item = QTreeWidgetItem(item)
                child_item.setText(0, subcategories)
                # print(os.path.isfile(subcategories),subcategories)
                child_item.setData(0,Qt.UserRole,[NodeType,f_path])
                child_item.setHidden(True)

def on_select(item,selected_category):
    """
    当树视图中选择项发生变化时更新选中的类别。
    """
    selected_item = item.text(0)  # 获取点击的项的文本
    parent_item = item.parent()
    while parent_item:
        parent_category = parent_item.text(0)
        selected_item = parent_category + SEPARATOR + selected_item
        parent_item = parent_item.parent()
    if DEFAULT_IMAGE_FORMAT + "-" in selected_item:
        selected_item = selected_item.split(DEFAULT_IMAGE_FORMAT + "-")[-1]
    selected_category.setText(selected_item)
def search_in_tree(node, keywords):
    """
    在树形结构中搜索包含关键词的叶子节点
    """
    result = None
    # 将节点文本信息按照分隔符 "-" 分割
    current_node_text = (keywords.split("-"))[0]
    # print(tree.item(node, "text"),current_node_text,keywords)
    # 把被分隔开的文本合并成一个字符串
    next_keywords = "-".join(keywords.split("-")[1:])
    if keywords == node.text(0):
        return node
    for child_index in range(node.childCount()):
        child = node.child(child_index)
        if current_node_text == child.text(0):
            if DEFAULT_IMAGE_FORMAT in child.text(0):
                return child
            return search_in_tree(child, next_keywords)
    # return result

def search(tree, entry_path, selected_category, entry_filename, show_image):
    """
    根据给定的类别和文件名执行搜索。
    """
    # 获取待索引目录路径
    directory_to_index = entry_path.text()
    
    # 获取已选择的类别，以 SEPARATOR 分隔
    if DEFAULT_IMAGE_FORMAT in selected_category.text():
        QMessageBox.information(None, "错误", "请选择类别")
        return
    # 获取输入的文件名
    search_filename = entry_filename.text()
    # 检查是否选择了目录
    if not directory_to_index:
        QMessageBox.critical(None, "错误", "请选择目录")
        return
    # 检查是否输入了文件名
    if not search_filename:
        QMessageBox.critical(None, "错误", "请输入文件名")
        return

    # 组合完整的文件名
    full_name = selected_category.text() + SEPARATOR + search_filename + DEFAULT_IMAGE_FORMAT
    
    # 在树中搜索文件节点
    result = []
    first_name = full_name.split("-")[0]
    for node in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(node)
        if first_name == item.text(0):
            result.append(search_in_tree(item, "-".join(full_name.split("-")[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if result[0]:
        filepath = result[0].data(0, Qt.UserRole)[1]
        show_image(filepath,result[0])

def get_all_child_nodes(item):
    """
    返回给定树视图项的所有子节点的列表。
    """
    child_nodes = []
    child_count = item.childCount()
    for i in range(child_count):
        child = item.child(i)
        item_data=child.data(0,Qt.UserRole)
        if item_data[0]=="photo" :
            child_nodes.append(item_data[1])
        # child_nodes.append(child)
        # 递归获取孙节点及其后代
        child_nodes.extend(get_all_child_nodes(child))
    return child_nodes

# 主程序中搜索特定节点并获取其子节点
def search_and_get_subnodes(tree, target_node_text):
    """
    在树视图中搜索具有指定文本的节点，返回其所有子节点的列表。
    """
    each_cata=target_node_text.split(SEPARATOR)
    if hasattr(tree,'invisibleRootItem'):
        root = tree.invisibleRootItem()
    else:
        root = tree
    for cata in each_cata:
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == cata:
                if item.data(0, Qt.UserRole)[0] == "photo":
                    return [item.data(0, Qt.UserRole)[1]]
                return search_and_get_subnodes(item, SEPARATOR.join(each_cata[1:])) if len(each_cata)>1 else get_all_child_nodes(item)

    QMessageBox.information(None, "错误", f"未找到：'{target_node_text}'的内容")
    return []

def global_search(tree, entry_path, entry_global_search, show_image):
    """
    执行全局搜索。
    """
    # 获取待索引目录路径
    directory_to_index = entry_path.text()
    
    # 获取输入的文件名
    search_filename = entry_global_search.text()

    # 检查是否选择了目录
    if not directory_to_index:
        QMessageBox.critical(None, "错误", "请选择目录")
        return

    # 检查是否输入了文件名
    if not search_filename:
        QMessageBox.critical(None, "错误", "请输入文件全名")
        return

    # 组合完整的文件名
    full_name = search_filename + DEFAULT_IMAGE_FORMAT
    
    # 在树中搜索文件节点
    result = []
    first_name = full_name.split("-")[0]
    for node in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(node)
        if first_name == item.text(0):
            result.append(search_in_tree(item, "-".join(full_name.split("-")[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if result[0]:
        filepath = result[0].data(0, Qt.UserRole)[1]
        show_image(filepath,result[0])

def update_image_format(entry_image_format, tree,directory):
    """
    更新默认图像格式。
    """
    global DEFAULT_IMAGE_FORMAT
    DEFAULT_IMAGE_FORMAT = entry_image_format.currentText()
    update_category_tree(tree,directory)

def update_sep(sep,tree,entry_path):
        global SEPARATOR
        SEPARATOR=sep.currentText()
        browse_directory(entry_path,tree,entry_path.text())

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

        self.re_current_local=False
        self.image_type = None

        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()

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
        self.next_button.setFixedHeight(25)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.local_button)
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
        self.windows.append(self)

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

    def timerEvent(self, event):
        # 自动播放下一张图片
        self.play_next_image()

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
        num_images_per_row = self.optimal_images_per_row(n,self.geometry().width(),self.geometry().height())
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
        self.resize_image_label()

    def resize_image_label(self):
        self.graphics_scene.clear()
        width = 0
        height = 0

        n=len(self.pixmaps)
        num_images_per_row = self.optimal_images_per_row(n,self.geometry().width(),self.geometry().height())
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
    def optimal_images_per_row(n,width=1000,height=1000):
        # Find the square root of the number of images to get an initial estimate
        sqrt_n = int(n ** 0.5)
        if sqrt_n == n**2:
            return sqrt_n
        num1 = sqrt_n
        num2 = sqrt_n+1
        
        if abs(num1*width-height*ceil(n/num1))<abs(num2*width-height*ceil(n/num2)):
            return num1
        else:
            return num2

# 默认配置
DEFAULT_CONFIG = {
    "window_size": [800, 600],
    "image_formats": [".png",".jpg",".svg",".jpeg",".bmp",".gif",".tiff"],
    "default_path": "images",
    "deault_visual_path": "visual_images",
}

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        self.save_config()

    def load_config(self):
        # 如果配置文件存在则加载配置，否则使用默认配置
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                # 忽略注释信息
                lines = f.readlines()
                json_data = "\n".join(line for line in lines if not line.strip().startswith("#"))
                return json.loads(json_data)
        else:
            return DEFAULT_CONFIG

    def save_config(self):
        # 保存当前配置到文件中
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("# 这是一个配置文件，用于存储程序的设置\n")
            f.write("# 请不要修改本文件，除非你知道你在做什么！\n")
            f.write(json.dumps(self.config, indent=4, ensure_ascii=False))

    def get(self, key):
        # 获取配置项的值
        return self.config.get(key)

    def set(self, key, value):
        # 设置配置项的值
        self.config[key] = value


# draw_pic

import numpy as np
import pandas as pd
# def draw_pic(file_path,save_path):
#     # data = pd.DataFrame(np.random.randn(100, 1), columns=['TEST_DATA'])
#     # data.to_csv(file_path, index=False)
#     # raw_data = pd.read_csv(file_path,sheet_name=0)
#     if file_path.endswith('.csv'):
#         raw_data = pd.read_csv(file_path)
#     elif file_path.endswith('.xlsx'):
#         raw_data = pd.read_excel(file_path,sheet_name=0)
#     title=list(raw_data.columns)
#     plot_data = np.array(raw_data.values).reshape(-1)
#     plt.plot(plot_data, linewidth=1.0)
#     plt.xticks(range(0, plot_data.shape[0], 10), fontsize=12)
#     plt.yticks(fontsize=12)
#     plt.legend(title, fontsize=12)
#     plt.show()
#     return plt

import pyqtgraph as pg
# class DrawWindow(QMainWindow):
#     windows=[]
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("数据可视化图形")
#         self.central_widget = QWidget()
#         self.setCentralWidget(self.central_widget)

#         layout = QVBoxLayout(self.central_widget)
#         # 设置反转色
#         pg.setConfigOption('background', 'w')#  设置背景色为白色
#         pg.setConfigOption('foreground', 'k')# 设置前景色为黑色
#         # 创建一个PlotWidget来显示折线图
#         self.plot_widget = pg.PlotWidget()
#         layout.addWidget(self.plot_widget)
#         self.plot_widget.addLegend(offset=(30, 30))
#         # self.plot_widget.setBackground( background='w')

#         # 创建标签用于显示坐标信息
#         self.coordinate_label = QLabel()
#         layout.addWidget(self.coordinate_label)

#         # 显示柱状图
#         self.bar_widget = pg.PlotWidget()
#         layout.addWidget(self.bar_widget)

#         # 初始化数据
#         self.x_data = []
#         self.y_data = []

#         # 设置坐标轴标签
#         self.plot_widget.setLabel('bottom', 'X轴')
#         self.plot_widget.setLabel('left', 'Y轴')
#         self.plot_widget.setTitle('折线图')

#         # 连接鼠标移动事件
#         self.plot_widget.scene().sigMouseMoved.connect(self.mouse_moved)
#         self.windows.append(self)
#     def mouse_moved(self, pos):
#         if self.plot_widget.sceneBoundingRect().contains(pos):
#             mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
#             x = mouse_point.x()
#             y = mouse_point.y()
#             self.coordinate_label.setText(f"坐标：({x:.2f}, {y:.2f})")
    
#     def draw_pic(self,file_path):
#         if file_path.endswith('.csv'):
#             raw_data = pd.read_csv(file_path)
#         elif file_path.endswith('.xlsx'):
#             raw_data = pd.read_excel(file_path,sheet_name=0)
#         title=list(raw_data.columns)
#         plot_data = np.array(raw_data.values).reshape(-1)
#         self.plot_widget.plot(plot_data,pen='k',antialias=True,name=title[0])
#         self.show()
    
#     # 绘制柱状图
#     def draw_bar(self,file_path):
#         if file_path.endswith('.csv'):
#             raw_data = pd.read_csv(file_path)
#         elif file_path.endswith('.xlsx'):
#             raw_data = pd.read_excel(file_path,sheet_name=0)
#         title=list(raw_data.columns)
#         plot_data = np.array(raw_data.values).reshape(-1)
#         self.bar_widget.plot(plot_data, pen='k', stepMode=True, fillLevel=0, brush=(0, 0, 255, 150),name=title[0])
#         self.show()
#     def closeEvent(self, event):
#         # 重写closeEvent方法，在窗口关闭时执行
#         # 从类属性中移除当前实例
#         DrawWindow.windows.remove(self)
#         event.accept()

#     @classmethod
#     def close_all(cls):
#         # 静态方法，关闭所有窗口
#         for window in cls.windows:
#             window.close()


class DrawWindow(QMainWindow):
    windows=[]
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据可视化图形")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # layout = QVBoxLayout(self.central_widget)
        self.playout = QGridLayout(self.central_widget)
        # 设置反转色
        pg.setConfigOption('background', 'w')#  设置背景色为白色
        pg.setConfigOption('foreground', 'k')# 设置前景色为黑色
        # 创建一个PlotWidget来显示折线图
        self.plot_widget = pg.PlotWidget()
        self.playout.addWidget(self.plot_widget,0,0)
        self.plot_widget.addLegend(offset=(30, 30))
        # self.plot_widget.setBackground( background='w')

        # 创建标签用于显示坐标信息
        self.coordinate_label = QLabel()
        self.playout.addWidget(self.coordinate_label,1,0)

        bu_get=QWidget()
        self.buttons=QHBoxLayout()
        bu_get.setLayout(self.buttons)
        #增加按钮
        self.add_button = QPushButton("散点图")
        self.button0 = QPushButton("折线图")
        self.button1 = QPushButton("柱状图")
        
        self.buttons.addWidget(self.add_button)
        self.buttons.addWidget(self.button0)
        self.buttons.addWidget(self.button1)
        self.playout.addWidget(bu_get,2,0)

        self.hist_button = QPushButton("直方图")
        self.buttons.addWidget(self.hist_button)
        self.hist_button.clicked.connect(self.draw_hist)
        self.add_button.clicked.connect(self.draw_sca)
        self.button0.clicked.connect(self.draw_line)
        self.button1.clicked.connect(self.draw_bar)

        # 初始化数据
        self.x_data = []
        self.y_data = []

        # 设置坐标轴标签
        self.plot_widget.setLabel('bottom', 'X轴')
        self.plot_widget.setLabel('left', 'Y轴')
        self.plot_widget.setTitle('折线图')

        # 连接鼠标移动事件
        self.plot_widget.scene().sigMouseMoved.connect(self.mouse_moved)
        self.windows.append(self)
    def mouse_moved(self, pos):
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self.coordinate_label.setText(f"坐标：({x:.2f}, {y:.2f})")
    
    def draw_pic(self,file_path):
        if file_path.endswith('.csv'):
            raw_data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            raw_data = pd.read_excel(file_path,sheet_name=0)
        self.title=list(raw_data.columns)
        self.plot_data = np.array(raw_data.values).reshape(-1)
        x = np.arange(len(self.plot_data))
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.plot(x,self.plot_data,pen='k',antialias=True,name=self.title[0])
        self.show()

    # 绘制折线图
    def draw_line(self):
        self.plot_widget.clear()
        if hasattr(self, 'plot_data'):
            title = self.title[0]
            plot_data = self.plot_data
            x = np.arange(len(plot_data))
            self.plot_widget.addLegend(offset=(30, 30))
            self.plot_widget.showGrid(x=True, y=True)
            self.plot_widget.plot(x,plot_data, pen='k', name=title,antialias=True)
            self.plot_widget.setLabel('bottom', 'X轴')
            self.plot_widget.setLabel('left', 'Y轴')
            self.plot_widget.setTitle('折线图')
            self.playout.addWidget(self.plot_widget, 0, 0)
            self.plot_widget.show()
    # 绘制散点图
    def draw_sca(self):
        self.plot_widget.clear()
        if hasattr(self, 'plot_data'):
            # self.plot_widget.hide()
            title = self.title[0]
            plot_data = self.plot_data
            x = np.arange(len(plot_data))
            self.plot_widget.addLegend(offset=(30, 30))
            self.plot_widget.showGrid(x=True, y=True)
            self.plot_widget.plot(x, plot_data, pen=None, symbol='t', symbolBrush=(0, 0, 255, 150), symbolSize=20,
                                 name=title)
            self.plot_widget.setLabel('bottom', 'X轴')
            self.plot_widget.setLabel('left', 'Y轴')
            self.plot_widget.setTitle('散点图')
            self.playout.addWidget(self.plot_widget, 0, 0)
            self.plot_widget.show()

    # 绘制柱状图
    def draw_bar(self):
        self.plot_widget.clear()
        if hasattr(self, 'plot_data'):
            # self.plot_widget.hide()
            title = self.title[0]
            plot_data = self.plot_data
            x = np.arange(len(plot_data))
            self.plot_widget.addLegend(offset=(30, 30))
            self.plot_widget.showGrid(x=True, y=True)
            # 使用BarGraphItem绘制柱状图
            bars = pg.BarGraphItem(x=x, height=plot_data, width=0.6, brush=(0, 0, 255, 150))
            self.plot_widget.addItem(bars)
            self.plot_widget.setLabel('bottom', 'X轴')
            self.plot_widget.setLabel('left', 'Y轴')
            self.plot_widget.setTitle('柱状图')
            self.playout.addWidget(self.plot_widget, 0, 0)
            self.plot_widget.show()


    # 绘制直方图
    def draw_hist(self):
        self.plot_widget.clear()
        
        if hasattr(self, 'plot_data'):
            plot_data = self.plot_data
            # 计算数据的直方图
            hist, bins = np.histogram(plot_data, bins='auto')
            # 创建直方图对象
            # colors = ['b','g','r','c','m','y','k','w']
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            # 计算每个方块的宽度和位置
            bar_width = (bins[1] - bins[0])
            bar_centers = (bins[:-1] + bins[1:]) / 2  # 方块中心位置为每个区域的中心
            # 创建直方图对象，并设置每个区域的颜色
            for i, (h, center) in enumerate(zip(hist, bar_centers)):
                hist_item = pg.BarGraphItem(x=[center], height=[h], width=bar_width, brush=colors[i % len(colors)])
                self.plot_widget.addItem(hist_item)
            # 设置 x 轴和 y 轴标签
            self.plot_widget.setLabel('bottom', '数值')
            self.plot_widget.setLabel('left', '频数')
            self.plot_widget.showGrid(x=True, y=True)
            # 设置标题
            self.plot_widget.setTitle('直方图')
            # 隐藏或显示其他部件
            self.plot_widget.show()
    def closeEvent(self, event):
        # 重写closeEvent方法，在窗口关闭时执行
        # 从类属性中移除当前实例
        DrawWindow.windows.remove(self)
        event.accept()

    @classmethod
    def close_all(cls):
        # 静态方法，关闭所有窗口
        for window in cls.windows:
            window.close()