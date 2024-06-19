from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QFileDialog,QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel,  QHBoxLayout, QGridLayout,  QComboBox,QCheckBox,QScrollArea,QAction,QMessageBox,QMenu,QInputDialog,QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys
import os

from utils.func import *
from conf.config import ConfigManager
from utils.data_visual import DrawWindow
from utils.ImageViewer import ShowImage,MultiImageDisplay,MutiShowImage

PATH_INDEX=r"conf\index_image.pkl"
PATH_CONFIG=r"conf\config.json"
# PyQt5
# 打包命令
'''
pyinstaller --onefile --noconsole index_search\\Index_search.py
'''
'''
Nuitka 打包

python -m nuitka --standalone --mingw64 --onefile ^
    --remove-output ^
    --disable-console ^
    --plugin-enable=pyqt5 ^
    --output-dir=dist ^
    --output-filename=a.exe ^
    Index_search_Qt.py
'''
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 获取当前文件所在目录
        self.current_dir=os.path.dirname(sys.argv[0])
        Config.current_dir = self.current_dir
        Config.index_file_path = os.path.join(self.current_dir,PATH_INDEX)
        conf_dir = os.path.join(self.current_dir, "conf")
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        # 配置文件路径
        self.config_file = os.path.join(self.current_dir, PATH_CONFIG)
        
        # 创建配置管理器并加载配置
        self.config_manager = ConfigManager(self.config_file)
        
        Config.ELEMENTS_TRANSLATION=self.config_manager.get("elements_translation")

        self.default_path=os.path.join(self.current_dir,self.config_manager.get("default_path"))
        self.checkboxes = []
        self.last_level_options = [] 
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("北极海冰图集电子管理器")
        # 设置图标
        # self.setWindowIcon(QIcon(os.path.join(self.current_dir, 'icons', 'icon.png')))
        size=self.config_manager.get("window_size")
        self.resize(size[0],size[1])

        self.select_node=QTreeWidgetItem(None)
        
        # 创建标签用于显示目录路径
        self.label_path = QLabel("文件目录:")
        self.entry_path = QLineEdit()
        self.button_browse = QPushButton("浏览")

        # 创建树形视图
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["目录"])

        # 创建标签显示文件名
        self.label_filename = QLabel("类中搜索:")
        self.entry_filename = QLineEdit()
        self.entry_filename.setPlaceholderText("选中类别后输入截断后的图片名称(A_B_C_D,选中B,输入C_D)")
        self.button_search = QPushButton("局部搜索")
        self.button_search.setToolTip('在选中类别下的图片中进行搜索')

        
        # 创建标签显示图片格式
        self.label_image_format = QLabel("图片格式:")
        self.image_format_commbox=QComboBox()
        # 可能的文件格式
        for format in self.config_manager.get("image_formats"):
            self.image_format_commbox.addItem(format)

        self.button_update_format = QPushButton("更新")
        
        # 设置分隔符
        self.label_sep=QLabel("分隔符")
        self.sep=QComboBox()
        self.sep.addItem("_")
        self.sep.addItem("-")
        
        format_sep_layout=QHBoxLayout()
        format_sep_layout.addWidget(self.image_format_commbox)
        format_sep_layout.addWidget(self.sep)
        
        merge_widget=QWidget()
        merge_widget.setLayout(format_sep_layout)
        
        # 创建搜索栏标签和输入框
        self.label_search = QLabel("搜索栏:")
        self.entry_global_search = QLineEdit()
        self.entry_global_search.setPlaceholderText("输入完整图片名称")
        self.button_global_search = QPushButton("全局搜索")
        self.button_global_search.setToolTip('在所有图片中进行搜索')

        # 创建时间间隔标签和输入框
        self.time_label = QLabel("播放速度(秒):")
        self.time_entry = QLineEdit()
        self.time_entry.setPlaceholderText("输入自动播放的时间间隔")
        self.time_entry.setText("0.1")  # 默认时间间隔为0.1秒
        
        # 选中的类别
        self.selected_category = QLabel("")
        self.selected_category.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.selected_category.setAlignment(Qt.AlignCenter)
        
        # 可视化文件
        self.button_load_file = QPushButton("可视化")
        self.button_load_file.setToolTip('加载文件进行数据可视化')
        
        # 显示多张图片
        self.button_multi_image = QPushButton("显示多张图片")

        # 创建多图显示搜索栏标签和输入框
        self.entry_elemets = QLineEdit()
        self.entry_elemets.setPlaceholderText("输入要素简写,以逗号分隔(SIV,SIC)")
        self.entry_muti_search = QLineEdit()
        self.entry_muti_search.setPlaceholderText("输入搜索日期")
        muti_search=QHBoxLayout()
        muti_search.addWidget(self.entry_elemets)
        muti_search.addWidget(self.entry_muti_search)
        self.muti_search=QWidget()
        self.muti_search.setLayout(muti_search)
        self.last_input=""

        self.checkbox_layout=QGridLayout()
        checkbox_widget=QWidget()
        checkbox_widget.setLayout(self.checkbox_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(checkbox_widget)
        # self.scroll_area.setFixedHeight(50)
        self.main_layout=QGridLayout()
        self.main_layout.addWidget(self.label_path,0,0)
        self.main_layout.addWidget(self.entry_path,0,1)
        self.main_layout.addWidget(self.button_browse,0,2)
        self.main_layout.addWidget(self.tree,1,0,1,3)
        self.main_layout.addWidget(self.selected_category,2,0,1,3)
        self.main_layout.addWidget(self.label_filename,3,0)
        self.main_layout.addWidget(self.entry_filename,3,1)
        self.main_layout.addWidget(self.button_search,3,2)
        self.main_layout.addWidget(self.label_image_format,4,0)
        

        self.main_layout.addWidget(merge_widget,4,1)
        self.main_layout.addWidget(self.label_sep,4,2,alignment=Qt.AlignCenter)

        self.main_layout.addWidget(self.label_search,5,0)
        self.main_layout.addWidget(self.entry_global_search,5,1)
        self.main_layout.addWidget(self.button_global_search,5,2)
        self.main_layout.addWidget(self.time_label,6,0)
        self.main_layout.addWidget(self.time_entry,6,1)
        self.main_layout.addWidget(self.button_load_file,6,2)

        self.main_layout.addWidget(self.button_multi_image,7,2)
        self.main_layout.addWidget(self.muti_search,7,1)
        self.scroll_area.setFixedHeight(40)
        self.main_layout.addWidget(self.scroll_area,8,0,1,3)

        # self.init_combs()
        
        # 创建主窗口部件并设置布局
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # 添加信号槽连接
        self.button_browse.clicked.connect(self.browse_directory) # 点击浏览按钮，选择文件夹
        self.button_search.clicked.connect(self.search) # 点击搜索按钮，搜索文件
        self.button_global_search.clicked.connect(self.global_search) # 点击全局搜索按钮，全局搜索
        self.tree.itemClicked.connect(self.on_select)# 点击树形视图节点，选中节点
        self.tree.itemDoubleClicked.connect(self.doubel_click)# 双击树形视图节点，显示图片
        self.button_load_file.clicked.connect(self.load_file)# 点击可视化按钮，加载文件
        self.button_multi_image.clicked.connect(self.show_multi_images) # 点击显示多张图片按钮，显示多张图片
        self.image_format_commbox.activated[str].connect(self.update_image_format)
        self.sep.activated[str].connect(self.update_sep)

        self.browse_directory(self.default_path)

        self.data = load_index_image(Config.index_file_path)

    def update_checkboxes(self, dicts):
        self.hide_last_level_options()
        for i, ops in enumerate(dicts):
            for j, op in enumerate(ops):
                checkbox = QCheckBox(op)
                checkbox.setChecked(True)
                checkbox.setProperty("parent", None)
                self.checkbox_layout.addWidget(checkbox, j, i)
                self.checkboxes.append(checkbox)
        
        row_count = self.checkbox_layout.rowCount()
        self.scroll_area.setFixedHeight(row_count * (self.checkboxes[0].sizeHint().height() + 10))

    # def init_combs(self):
    #     self.combos = []
    #     self.data = load_index_image(Config.index_file_path)
    #     combs_widget = QWidget()
    #     self.combos_layout = QHBoxLayout()
    #     self.create_combos(self.data, 0)
    #     combs_widget.setLayout(self.combos_layout)
    #     roll_area = QScrollArea()
    #     roll_area.setWidgetResizable(True)
    #     roll_area.setFixedHeight(combs_widget.sizeHint().height()+20)
    #     roll_area.setWidget(combs_widget)
    #     self.main_layout.addWidget(roll_area, 9, 1)
    # def clear_combos_layout(self):
    #     for combo in self.combos:
    #         combo.deleteLater()
    #     self.combos = []
    # def create_combos(self, current_data, level):
    #     if level >= 3:
    #         return
    #     if isinstance(current_data, dict) and current_data != {}:
    #         combo = QComboBox()
    #         combo.addItem('请选择')
    #         combo.addItems(current_data.keys())
    #         combo.setProperty("property",[0,None])
    #         combo.currentIndexChanged.connect(lambda index, lvl=level: self.update_combos(index, lvl))
    #         combo.setEnabled(len(self.combos) == 0)
    #         self.combos_layout.addWidget(combo)
    #         self.combos.append(combo)
            
    #         deepest_data = None
    #         for value in current_data.values():
    #             if self.get_dict_depth(value) > self.get_dict_depth(deepest_data):
    #                 deepest_data = value
    #         if deepest_data:
    #             # print(deepest_data)
    #             self.create_combos(deepest_data, level + 1)
    #             return
    #     elif isinstance(current_data, str):
    #         pass
    #     else:
    #         # 如果数据不是字典也不是字符串，不创建新的下拉框
    #         return
    # def update_combos(self, index, level):
    #     if index > 0:
    #         key = self.combos[level].currentText()
    #         next_level_data = self.data
    #         for lvl in range(level):
    #             next_level_data = next_level_data[self.combos[lvl].currentText()]
    #         # 现在找到了当前选项在字典中的位置
    #         next_level_data = next_level_data[key]

    #         if isinstance(next_level_data, dict) and level < len(self.combos) - 1:
    #             self.combos[level + 1].clear()
    #             self.combos[level + 1].addItem('请选择')
    #             self.combos[level + 1].addItems(next_level_data.keys())
    #             # 计算文本选项的最大宽度
    #             # self.combos[level+1].setFixedWidth(max_width+20)

    #             self.combos[level + 1].setEnabled(True)
    #             combo = self.combos[level + 1]

    #             if level+1 < len(self.combos):
    #                 # and DEFAULT_IMAGE_FORMAT in self.combos[level+1].itemText(1):
    #                 #     self.combos[level].setProperty("property",[1,list(next_level_data.values())])
    #                 al=list(next_level_data.values())
    #                 tar=[]
    #                 if al:
    #                     for i in range(1,combo.count()):
    #                         if DEFAULT_IMAGE_FORMAT in combo.itemText(i):
    #                             tar.append(al[i-1])
    #                 self.combos[level].setProperty("property",[1,tar])
    #             # 递归地禁用所有更深层级的下拉框
    #             for combo in self.combos[level + 2:]:
    #                 combo.clear()
    #                 combo.addItem('请选择')
    #                 combo.setEnabled(False)
    #             if DEFAULT_IMAGE_FORMAT in self.combos[level+1].itemText(1):
    #                 self.combos[level+1].setProperty("property",[1,None])
    #         else:
    #             # 禁用所有更深层级的下拉框
    #             for combo in self.combos[level + 1:]:
    #                 combo.clear()
    #                 combo.addItem('请选择')
    #                 combo.setEnabled(False)
    #     else:
    #         # 当选择"请选择"时，禁用所有更深层级的下拉框
    #         self.combos[level].setProperty("property",[0,None])
    #         for combo in self.combos[level + 1:]:
    #             combo.clear()
    #             combo.addItem('请选择')
    #             combo.setEnabled(False)
    #     if level < len(self.combos)-1:
    #         mxa_len, v_len = 0, 0
    #         comboBox = self.combos[level + 1]
    #         for y in range(0, comboBox.count()):
    #             v_len=comboBox.fontMetrics().width(comboBox.itemText(y))
    #             if (mxa_len <= v_len): 
    #                 mxa_len = v_len
    #         comboBox.view().setMinimumWidth(int(mxa_len+15))	# 设置自适应宽度
    #     # for co in self.combos:
    #         # print(co.currentText(),'\t',co.property("property"),end='\n')
    #     # print("#"*100)
    #     # self.show_last_level_options()
    # def get_dict_depth(self, data):
    #     """递归函数计算字典的最大深度"""
    #     if isinstance(data, dict) and data:
    #         return 1 + max((self.get_dict_depth(value) for value in data.values()), default=0)
    #     else:
    #         return 0

    def show_last_level_options(self):
        self.hide_last_level_options()
        l_level=-1
        combo = self.combos[l_level]
        while combo.count()==1:
            l_level=l_level-1
            combo = self.combos[l_level]
        # if DEFAULT_IMAGE_FORMAT not in combo.itemText(1):
        #     return
        self.last_level_options.clear()
        for i in range(1,combo.count()):
            if DEFAULT_IMAGE_FORMAT in combo.itemText(i):
                self.last_level_options.append(combo.itemText(i))
        for option in self.last_level_options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(True)
            checkbox.setProperty("path", option)
            # print(checkbox.text())
            self.checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)


    def hide_last_level_options(self):
        for checkbox in self.checkboxes:
            checkbox.deleteLater()
        self.checkboxes.clear()
        self.scroll_area.setFixedHeight(40)

    def browse_directory(self,image_path=None):
        directory_path = image_path or QFileDialog.getExistingDirectory()
        if directory_path:
            self.entry_path.setText(directory_path)
            self.indexing_thread = IndexingThread(directory_path, DEFAULT_IMAGE_FORMAT)
            self.indexing_thread.indexing_done.connect(self.on_indexing_done)
            self.indexing_thread.error_signal.connect(self.on_error)
            self.indexing_thread.start()
        self.data = load_index_image(Config.index_file_path)
    def on_indexing_done(self, category_index):
        self.tree.clear()
        update_treeview(self.tree, self.tree, category_index)
    def on_error(self, message):
        self.tree.clear()
        QMessageBox.critical(self, "错误", message)
    def search(self):
        search(self.tree, self.entry_path, self.selected_category, self.entry_filename, self.show_image)
    def update_image_format(self):
        update_image_format(self.image_format_commbox,self.tree,self.entry_path.text())
        self.data = load_index_image(Config.index_file_path)

    def update_sep(self):
        update_sep(self.sep)
        self.browse_directory(self.entry_path.text())
        self.data = load_index_image(Config.index_file_path)

    def global_search(self):
        global_search(self.tree,self.entry_path,self.entry_global_search,self.show_image)

    def on_select(self,item):
        on_select(item,self.selected_category)
        self.select_node=item
    def show_image(self,path,Node):
        Simg=ShowImage(self.tree,self.time_entry)
        Simg.show_image(path)
        Simg.current_Node=Node
    def doubel_click(self):
        item_data=self.select_node.data(0,Qt.UserRole)
        if item_data and item_data[0] in ['file', 'photo']:
            self.show_image(item_data[1], self.select_node)
    def load_file(self):
        #读取文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;所有文件(*)")# 文本文件 (*.txt);;*.xls所有文件 (*)
        if file_path:
            # 在这里执行读取文件和数据可视化的操作
            self.visualize_data(file_path)
    def visualize_data(self,file_path):
        # 默认保存位置
        # save_path = os.path.join(self.current_dir,self.config_manager.get("deault_visual_path"))
        # 显示消息框
        draw_window = DrawWindow()
        draw_window.draw_pic(file_path)

    def show_multi_images(self):
        c=self.getInputType()
        # 显示多张图片
        if self.entry_muti_search.text() == "":
            self.hide_last_level_options()
            return
        if not c:
            return
        elements=list(self.config_manager.get("elements_translation").keys())
        # input_elements=self.entry_elemets.text().replace('，',',').split(",")
        input_elements = [e.strip() for e in self.entry_elemets.text().replace('，',',').split(",") if e.strip()]
        # print(input_elements)
        for i in input_elements:
            if i not in elements and i!="":
                elements.append(i)
        dicts,self.paths,items = muti_search(self.entry_path,self.entry_muti_search,self.data,elements,self.tree,c)
        if dicts is None:
            return
        if self.last_input != self.entry_muti_search.text():
            self.update_checkboxes(dicts)
        self.last_input=self.entry_muti_search.text()
        
        image_paths = [path for i, path in enumerate(self.paths) if self.checkboxes[i].isChecked() and path is not None]
        c_name = [name for category in dicts for name in category]
        
        if image_paths:
            # multi_image_display = MultiImageDisplay()
            multi_image_display = MutiShowImage(tree=self.tree,time_entry=self.time_entry,image_paths=image_paths)
            multi_image_display.check_names=c_name
            multi_image_display.current_Nodes=items
            multi_image_display.show_images(image_paths)
    def getInputType(self):
        items = ["A", "B"]
        item, ok = QInputDialog.getItem(self, " ", "请选择图类", items, editable=False)
        if ok and item:
            return item
        else:
            return None

    def closeEvent(self, event):
        DrawWindow.close_all()
        ShowImage.close_all()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # import time
    # start_time = time.perf_counter()
    window = MainWindow()
    window.show()
    # end_time = time.perf_counter()
    # print(end_time-start_time)
    sys.exit(app.exec_())