import pickle
from PyQt5.QtWidgets import  QFileDialog, QMessageBox, QTreeWidgetItem,QTreeWidget
from PyQt5.QtCore import Qt,QThread, pyqtSignal
import copy
import os
import re
import datetime
class CONFIG():
    def __init__(self):
        self.current_dir=None # 主文件所在目录
        self.ELEMENTS_TRANSLATION=None # 中文名称转换
        self.index_file_path=None # 索引文件路径
        self.circles_path=None # 图片圆形位置
        self.no_lon_lat=None # 无经纬度要素
        self.extra_directory=None # 额外索引目录

Config=CONFIG()
# 初始文件格式
DEFAULT_IMAGE_FORMAT = ".jpg" #[".jpg", ".jpeg", ".png"]
SEPARATOR = "_" # 默认分隔符
NAME_SPACE=SEPARATOR+'空间分布图'
NAME_TIME=SEPARATOR+'时间序列图'

class NodeType:
    CATEGORY = "category"
    PHOTO = "photo"
    FILE = "file"


def get_start_date(search_date_str):
    """
    根据搜索日期返回对应的五天间隔的起始日期。
    """
    # 将字符串转换为日期对象
    search_date = datetime.datetime.strptime(search_date_str, '%Y_%m_%d')
    
    # 找到2011_01_01作为基准日期
    base_date = datetime.datetime(2011, 1, 1)
    
    # 计算搜索日期和基准日期之间的天数差
    delta_days = (search_date - base_date).days
    
    # 计算属于的五天间隔的起始日期
    start_date = base_date + datetime.timedelta(days=(delta_days // 5) * 5)
    
    return start_date.strftime('%Y_%m_%d')

def get_end_date(search_date_str):
    """
    根据搜索日期返回对应的五天间隔的结束日期。
    """
    # 将字符串转换为日期对象
    search_date = datetime.datetime.strptime(search_date_str, '%Y_%m_%d')
    
    # 找到2011_01_01作为基准日期
    base_date = datetime.datetime(2011, 1, 1)
    
    # 计算搜索日期和基准日期之间的天数差
    delta_days = (search_date - base_date).days
    
    # 计算属于的五天间隔的起始日期
    start_date = base_date + datetime.timedelta(days=(delta_days // 5) * 5)
    
    # 计算五天间隔的结束日期
    end_date = start_date + datetime.timedelta(days=4)
    
    return end_date.strftime('%Y_%m_%d')

def chinese_to_arabic_sort(arr):
    chinese_numbers= {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": "","百": "","千": "","万": "","亿": ""}
    arrb=copy.deepcopy(arr)
    sorted_b=arrb
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

def update_category_tree(tree, directory_to_index):
    if not directory_to_index:
        return
    # 清空原有树视图
    tree.clear()
    category_index = index_image_files(directory_to_index, DEFAULT_IMAGE_FORMAT)
    update_treeview(tree, tree, category_index)

def update_treeview(tree, parent, categories): # 修改中文名称
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
            # 确保得到正确的文件路径
            f_path = f_path.replace(NAME_SPACE,'')
            f_path = f_path.replace(NAME_TIME,'')
            NodeType = "photo"
        item = QTreeWidgetItem(parent)
        
        # 修改中文名称显示
        dic=Config.ELEMENTS_TRANSLATION
        item.setText(0, category)
        for k,v in dic.items():
            if k in category:
                # print(k,v)
                item.setText(0, category.replace(k,v))
                break

        item.setData(0,Qt.UserRole,[NodeType,f_path])
        if isinstance(subcategories, dict):
            update_treeview(tree, item, subcategories)
        else:
            if type(subcategories) is str:
                f_path = subcategories
                # 确保得到正确的文件路径
                f_path = f_path.replace(NAME_SPACE,'')
                f_path = f_path.replace(NAME_TIME,'')
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
    if DEFAULT_IMAGE_FORMAT + SEPARATOR in selected_item:
        selected_item = selected_item.split(DEFAULT_IMAGE_FORMAT + SEPARATOR)[-1]
    selected_category.setText(selected_item)
def search_in_tree(node, keywords):
    """
    在树形结构中搜索包含关键词的叶子节点
    """
    result = None
    # 将节点文本信息按照分隔符 SEPORATOR 分割

    current_node_text = (keywords.split(SEPARATOR))[0]
        
    # print(tree.item(node, "text"),current_node_text,keywords)
    # 把被分隔开的文本合并成一个字符串
    next_keywords = SEPARATOR.join(keywords.split(SEPARATOR)[1:])
    if keywords == node.text(0):
        return node
    for child_index in range(node.childCount()):
        child = node.child(child_index)
        if current_node_text == child.text(0):
            if DEFAULT_IMAGE_FORMAT in child.text(0):
                return child
            return search_in_tree(child, next_keywords)
    return result

def search(tree, entry_path, selected_category, entry_filename, show_image):  # 修改中文名称
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
    for k,v in Config.ELEMENTS_TRANSLATION.items():
        full_name=full_name.replace(k,v)
    # 在树中搜索文件节点
    result = []
    first_name = full_name.split(SEPARATOR)[0]
    for node in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(node)
        if first_name == item.text(0):
            result.append(search_in_tree(item, SEPARATOR.join(full_name.split(SEPARATOR)[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if len(result)>0:
        if result[0]:
            filepath = result[0].data(0, Qt.UserRole)[1]
            show_image(filepath,result[0])

def global_search(tree, entry_path, entry_global_search, show_image): # 修改中文名称
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
    for k,v in Config.ELEMENTS_TRANSLATION.items():
        full_name=full_name.replace(k,v)
    # 在树中搜索文件节点
    result = []
    first_name = full_name.split(SEPARATOR)[0]
    for node in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(node)
        if first_name == item.text(0):
            result.append(search_in_tree(item, SEPARATOR.join(full_name.split(SEPARATOR)[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if len(result)>0:
        if result[0]:
            filepath = result[0].data(0, Qt.UserRole)[1]
            show_image(filepath,result[0])

def muti_search(entry_path, entry_date_search,index_dict,elements,tree,cate='A'):
    # elements=["SIC","SIT","SIH","SIE"]
    # 获取待索引目录路径
    directory_to_index = entry_path.text()
    # 获取输入的文件名
    search_filename = entry_date_search
    # 检查是否选择了目录
    if not directory_to_index:
        QMessageBox.critical(None, "错误", "请选择目录")
        return
    # 检查是search_filename是否是日期
    if not re.match(r'\d{4}'+SEPARATOR+r'\d{2}'+SEPARATOR+r'\d{2}', search_filename):
        QMessageBox.critical(None, "错误", "查询日期格式错误")
        return None,None,None
    dicts=[]
    for element in elements:
        # 组合完整的文件名
        al=[x for x in index_dict.keys() if element in x]
        if len(al)>0:
            dicts.append(al)
    result=[]
    end_name = search_filename + DEFAULT_IMAGE_FORMAT
    ids=end_name.split(SEPARATOR)
    ta_dic=[]   # 初始化复选框列表
    items=[]
    for start in dicts:
        if isinstance(start,list):
            ta=[]
            for head in start:
                for k,v in Config.ELEMENTS_TRANSLATION.items():
                    if k in head:
                        if cate=='':
                            search_ids=[head.replace(k,v),NAME_SPACE.replace(SEPARATOR,"")]+ids
                        else:
                            search_ids=[head.replace(k,v),NAME_SPACE.replace(SEPARATOR,""),cate]+ids
                        # print(search_ids)
                item=find_node_by_path(tree,search_ids)
                if item:
                    ta.append(head)
                    result.append(item.data(0, Qt.UserRole)[1])
                    items.append(item)
            ta_dic.append(ta)
    return ta_dic,result,items

def update_image_format(entry_image_format, tree,directory):
    """
    更新默认图像格式。
    """
    global DEFAULT_IMAGE_FORMAT
    DEFAULT_IMAGE_FORMAT = entry_image_format.currentText()
    update_category_tree(tree,directory)

def update_sep(sep):
        global SEPARATOR
        global NAME_SPACE
        global NAME_TIME
        SEPARATOR=sep.currentText()
        NAME_SPACE=SEPARATOR+'空间分布图'
        NAME_TIME=SEPARATOR+'时间序列图'
def find_node_by_path(tree, path):
    def find_node_recursive(item, path):
        if item is None or len(path)==0:
            return None
        for i in range(item.childCount()):
            child_item = item.child(i)
            # print(child_item.text(0),path)
            if child_item.text(0)==path[0]:
                if len(path)==1:
                    return child_item
                return find_node_recursive(child_item, path[1:])
        return None
    if isinstance(tree,QTreeWidget):
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item.text(0)==path[0]:
                # print(item.text(0))
                return find_node_recursive(item, path[1:])
    else:
        for i in range(tree.childCount()):
            item = tree.child(i)
            if item.text(0)==path[0]:
                return find_node_recursive(item, path[1:])
    return None


def save_index_image(index_image, path=Config.index_file_path):
    filename = path
    with open(filename, 'wb') as f:
        pickle.dump(index_image, f)

def load_index_image(path=Config.index_file_path):
    filename = path
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return None

class IndexingThread(QThread):
    indexing_done = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    def __init__(self, directory, image_format, parent=None):
        super().__init__(parent)
        self.directory = directory
        self.image_format = image_format

    def run(self):
        index = index_image_files(self.directory, self.image_format)
        if not index:
            self.error_signal.emit("未找到任何图像文件")
        else:
            self.indexing_done.emit(index)
def index_image_files(directory, image_format):
    # index = load_index_image(directory)
    # if index is not None:
    #     return index
    index = {}
    pattern = r'_\d{4}?' + image_format + '$'

    for root, dirs, files in os.walk(directory):
        files = sorted(files)
        for file in files:
            if file.endswith(image_format):
                if SEPARATOR not in file:
                    continue
                
                po = file.find(SEPARATOR)
                if re.search(pattern, file):
                    file = file[:po] + NAME_TIME + file[po:]
                else:
                    file = file[:po] + NAME_SPACE + file[po:]

                categories, filename = file.rsplit(SEPARATOR, maxsplit=1)
                categories = categories.strip().split(SEPARATOR)
                filename = filename.strip()

                curr_index = index
                for category in categories:
                    curr_index = curr_index.setdefault(category, {})

                curr_index[filename] = os.path.join(root, file)

    if not index:
        return {}

    save_index_image(index, Config.index_file_path)
    return index
