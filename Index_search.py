import copy
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk


# 打包命令
'''
pyinstaller --onefile --noconsole index_search\\Index_search.py
'''

# 默认图像格式
DEFAULT_IMAGE_FORMAT = ".png" #[".jpg", ".jpeg", ".png"]
# 默认分隔符
SEPARATOR = "-"


# 数据计算功能和可视化
# 图片同时展示(比如同时选中多个图,可以同时显示多个图),比如输入某个时间2021.9.1,同时出现当天的所有图


# 相对简单的排序
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
def index_image_files(directory, image_format) -> dict:
    """
    在给定目录中索引图像文件。
    返回一个字典，其中键是类别名称，值是包含文件名和路径的字典。
    参数:
    directory (str): 需要索引图像文件的目录路径。
    image_format (str): 需要索引的图像文件的格式，如".jpg"或".png"。
    返回:
    dict: 键为类别名称的字典，其值为另一个字典，包含属于该类别的文件名和文件路径。
    """
    index = {}  # 初始化索引字典
    
    # 遍历目录及其子目录中的所有文件
    for root, dirs, files in os.walk(directory):
        files=chinese_to_arabic_sort(files)
        for file in files:
            # 如果文件以指定的图像格式结尾，则进行处理
            if file.endswith(image_format):
                # 根据文件名划分类别和文件名
                if SEPARATOR not in file:
                    messagebox.showinfo("错误",f"请按照以下格式输入图片名称: 类别1-类别2-...-类别n-图片名称\n例如: cat-dog-1"+DEFAULT_IMAGE_FORMAT)
                    return
                categories, filename = file.rsplit(SEPARATOR, maxsplit=1)
                categories = categories.strip().split(SEPARATOR)
                filename = filename.strip()
                
                curr_index = index  # 当前索引位置
                
                # 遍历类别，更新索引
                for category in categories:
                    curr_index = curr_index.setdefault(category, {})
                
                # 在相应的类别下记录文件名和完整路径
                curr_index[filename] = os.path.join(root, file)
    # print(index)
    if index == {}:
        messagebox.showinfo("错误",f"未找到规范格式的图片文件")
    # print(index)
    return index  # 返回索引字典
def browse_directory():
    """
    打开一个对话框，选择包含图像文件的目录。
    """
    directory_path = filedialog.askdirectory()
    if directory_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, directory_path)
        update_category_tree()

def update_category_tree():
    """
    使用索引的类别更新分类树视图。
    """
    directory_to_index = entry_path.get()
    if not directory_to_index:
        return
    # 清空原有树视图
    for item in tree.get_children():
        tree.delete(item)
    category_index = index_image_files(directory_to_index, DEFAULT_IMAGE_FORMAT)
    update_treeview(tree, "", category_index)

def update_treeview(tree, parent, categories):
    """
    递归地使用类别更新树视图。
    """
    # print("parent ",tree.item(parent,'text'),"categories ",categories)
    if not categories:
        return
    for category, subcategories in categories.items():
        # node_data = {"file_path": None,"NodeType":"category"}  # 存储文件路径
        f_path=None
        NodeType="category"
        if DEFAULT_IMAGE_FORMAT in category:
            f_path=categories[category]
            NodeType="photo"
        category_id = tree.insert(parent, "end", text=category, tags=(f_path,NodeType))
        if isinstance(subcategories, dict):
            update_treeview(tree, category_id, subcategories)
        else:
            if type(subcategories) is str:
                f_path=subcategories
                NodeType="file"
                tree.insert(category_id, "end", text=subcategories, tags=(f_path,NodeType))


def on_select(event):
    """
    监视鼠标箭头活动，当树视图中选择项发生变化时更新选中的类别。
    """
    item = tree.focus()
    global selected_node
    selected_node=item
    selected_category.set(tree.item(item, "text"))
    selected_item = selected_category.get()
    parent_item = tree.parent(item)
    while parent_item:
        parent_category = tree.item(parent_item, "text")
        selected_item=parent_category + SEPARATOR + selected_item
        parent_item =tree.parent(parent_item)
    if DEFAULT_IMAGE_FORMAT+"-" in selected_item:
        selected_item=selected_item.split(DEFAULT_IMAGE_FORMAT+"-")[-1]
    selected_category.set(selected_item)

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
    if keywords== tree.item(node, "text"):
        return node
    for child in tree.get_children(node):
        if current_node_text == tree.item(child, "text"):
            if DEFAULT_IMAGE_FORMAT in tree.item(child, "text"):
                return child
            return search_in_tree(child, next_keywords)
    # return result
def search():
    """
    根据给定的类别和文件名执行搜索。
    """
    # if tree.parent(selected_node) == "":
    # print(selected_node)
    # item_data = tree.item(selected_node, "tags")
    # print(item_data)  # 输出节点的标签（tag）
    # 获取待索引目录路径
    directory_to_index = entry_path.get()
    # 获取已选择的类别，以SEPARATOR分隔
    if DEFAULT_IMAGE_FORMAT in selected_category.get():
        messagebox.showinfo("错误",f"请选择类别")
        return
    categories = selected_category.get().split('-')
    # 获取输入的文件名
    search_filename = entry_filename.get()

    # print("categories&parent",categories)
    
    # 检查是否选择了目录
    if not directory_to_index:
        messagebox.showerror("错误", "请选择目录")
        return

    # 检查是否输入了文件名
    if not search_filename:
        messagebox.showerror("错误", "请输入文件名")
        return

    # 索引指定目录中的图像文件
    # image_index = index_image_files(directory_to_index, DEFAULT_IMAGE_FORMAT)
    
    # if SEPARATOR in search_filename:
    #     next_categories = search_filename.split(SEPARATOR)
    #     categories = categories + next_categories[:-1]
    #     search_filename = next_categories[-1]
    
    # # 在索引中搜索符合条件的图像文件
    # result = search_image_file(image_index, categories, search_filename, DEFAULT_IMAGE_FORMAT)
    
    allname=selected_category.get()+SEPARATOR+search_filename+DEFAULT_IMAGE_FORMAT
    # print("FullName",FullName)
    result = []
    firstname=allname.split("-")[0]
    for node in tree.get_children():
        if firstname == tree.item(node, "text"):
            result.append(search_in_tree(node, "-".join(allname.split("-")[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if result[0]:
        item_data = tree.item(result[0], "tags")
        filepath=item_data[0]
        Simg=ShowImage(root)
        Simg.current_Node=result[0]
        Simg.show_image(filepath) 
        # ShowImage(root).show_image(result)

        # 显示包含搜索结果信息的消息框
        # messagebox.showinfo("搜索结果", f"成功查询 {search_filename+DEFAULT_IMAGE_FORMAT} 属于类别 {'-'.join(categories)} 位于 {result}")
    else:
        # 如果未找到文件，显示相应的消息框
        messagebox.showinfo("搜索结果", f"File {search_filename} 在类别 {'-'.join(categories)} 中未发现该文件")
    # 在树形结构中搜索匹配的叶子节点
    # tree_search_results = []
    # for node in tree.get_children():
    #     tree_search_results.extend(search_in_tree(node, search_filename))

    # print(tree_search_results)
    # 将搜索结果高亮显示
    # for item in tree.get_children():
    #     if item in tree_search_results:
    #         tree.tag_configure(item, background="yellow")
    #     else:
    #         tree.tag_configure(item, background="white")
def global_search():
    """
    执行全局搜索。
    """
    # 获取待索引目录路径
    directory_to_index = entry_path.get()
    # 获取输入的文件名
    search_filename = entry_global_search.get()

    # 检查是否选择了目录
    if not directory_to_index:
        messagebox.showerror("错误", "请选择目录")
        return

    # 检查是否输入了文件名
    if not search_filename:
        messagebox.showerror("错误", "请输入文件全名")
        return

    # # 索引指定目录中的图像文件
    # image_index = index_image_files(directory_to_index, DEFAULT_IMAGE_FORMAT)
    
    # categories = search_filename.split('-')
    # # print("global categories",categories,categories[:-1],categories[-1])
    # result = search_image_file(image_index, categories[:-1], categories[-1], DEFAULT_IMAGE_FORMAT)
    
    allname=search_filename+DEFAULT_IMAGE_FORMAT
    result = []
    firstname=allname.split("-")[0]
    for node in tree.get_children():
        if firstname == tree.item(node, "text"):
            result.append(search_in_tree(node, "-".join(allname.split("-")[1:])))
            break

    # 如果找到了文件，显示搜索结果
    if result[0]:
        item_data = tree.item(result[0], "tags")
        filepath=item_data[0]
        Simg=ShowImage(root)
        Simg.current_Node=result[0]
        Simg.show_image(filepath) 
        # 显示包含搜索结果信息的消息框
        # messagebox.showinfo("全局搜索结果", f"查询到 {search_filename+DEFAULT_IMAGE_FORMAT} 属于类别 {'-'.join(categories)} 位于 {result}")
    else:
        # 如果未找到文件，显示相应的消息框
        messagebox.showinfo("全局搜索结果", f"未发现该文件")

def update_image_format():
    """
    更新默认图像格式。
    """
    global DEFAULT_IMAGE_FORMAT
    DEFAULT_IMAGE_FORMAT = entry_image_format.get()
    update_category_tree()

class ShowImage:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.label = None
        self.current_Node = None
        self.current_image=None
        self.time=float(time_entry.get()) # 播放每张图片间隔2秒
        self.playing=False
        self.timer_id = None
    def show_image(self,image_path):
            # 如果已经显示了一张图片，则直接更新显示的图片内容，而不是新建一个窗口
            if hasattr(self, "window") and self.window is not None:
                image = Image.open(image_path)
                photo = ImageTk.PhotoImage(image)
                self.label.configure(image=photo)
                self.label.image = photo
                return image

            new_window = tk.Toplevel(root)
            new_window.title("Image Viewer")
            new_window.geometry("800x600")  # 设置新窗口的默认大小
            
            def on_window_close():
                self.window=None
                self.label=None
                new_window.destroy()

            # 当窗口关闭时调用 on_window_close ,第二个参数应该是一个函数，而不是函数的返回值
            new_window.protocol("WM_DELETE_WINDOW", on_window_close)
            
            image = Image.open(image_path)
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(new_window, image=photo)
            # label.image = photo  # 保持图片对象的引用，避免被垃圾回收
            label.pack(expand=True, fill="both")  # 让图片充满整个窗口

            new_window.wm_attributes("-topmost", True)
            self.window=new_window
            self.label = label  # 将label对象保存在函数属性中，以便下次更新图片内容
            self.current_image_path = image_path  # 将当前显示的图片路径保存在函数属性中，以便下次更新图片内容
            self.image_name=image_path[image_path.find("\\")+1:]
            def resize_image(event):
                new_window.after(0, self.resize_image_label, event, label, image)
            label.bind("<Configure>", resize_image)
            self.add_controls(new_window)
            return image
    def add_controls(self, window):
        # 添加连播按钮
        self.prev_button = tk.Button(window, text="上一张", command=self.play_last_image)
        self.prev_button.pack(side="left", padx=10)
        self.next_button = tk.Button(window, text="下一张", command=self.play_next_image)
        self.next_button.pack(side="right", padx=10)
        self.play_button = tk.Button(window, text="自动播放", command=self.auto_play)
        self.play_button.pack(side="bottom", padx=10)
    def play_next_image(self):
        # 播放下一张图片逻辑
        next_node = tree.next(self.current_Node)
        while next_node and tree.item(next_node,"tags")[1]!="photo":
            if tree.item(next_node, "tags")[1] == "file":
                next_node = tree.parent(next_node)
            elif tree.item(next_node, "tags")[1] == "category":
                # next_node=self.select_from_category(next_node)
                while tree.item(next_node, "tags")[1] =="category":
                    next_node = tree.get_children(next_node)[0]
                    if not next_node:
                        break
            else:
                break

        if not next_node:
            # 当前节点没有相邻节点，尝试查找父节点的相邻节点
            parent_node = tree.parent(self.current_Node)
            while parent_node and tree.item(parent_node,"tags")[1]!="photo":
                next_node = tree.next(parent_node)
                if next_node and tree.item(next_node,"tags")[1]=="photo":
                    break
                if next_node and tree.item(next_node,"tags")[1]=="category":
                    # next_node=self.select_from_category(next_node)
                    while tree.item(next_node, "tags")[1] =="category":
                        next_node = tree.get_children(next_node)[0]
                    break
                parent_node = tree.parent(parent_node)

        if not next_node:
            # 未找到下一张图片，重新播放第一张图片
            next_node = tree.get_children("")[0]
            while tree.item(next_node, "tags")[1] != "photo":
                next_node = tree.get_children(next_node)[0]

        if next_node:
            # print(tree.item(next_node,"tags"))
            file_path = tree.item(next_node, "tags")[0]
            image = Image.open(file_path)
            photo = ImageTk.PhotoImage(image)
            self.label.configure(image=photo)
            self.label.image = photo
            self.current_Node = next_node
            self.current_image = image
            def resize_image(event):
                self.window.after(0, self.resize_image_label, event, self.label, image)
            self.label.bind("<Configure>", resize_image)
    def play_last_image(self):
        # 播放上一张图片逻辑
        prev_node = tree.prev(self.current_Node)
        while prev_node and tree.item(prev_node,"tags")[1]!="photo":
            if tree.item(prev_node, "tags")[1] == "file":
                prev_node = tree.parent(prev_node)
            elif tree.item(prev_node, "tags")[1] == "category":
                # prev_node=self.select_from_category(prev_node)
                while tree.item(prev_node, "tags")[1] =="category":
                    prev_node = tree.get_children(prev_node)[-1]
                    if not prev_node:
                        break
            else:
                break

        if not prev_node:
            # 当前节点没有相邻节点，尝试查找父节点的相邻节点
            parent_node = tree.parent(self.current_Node)
            while parent_node and tree.item(parent_node,"tags")[1]!="photo":
                prev_node = tree.prev(parent_node)
                if prev_node and tree.item(prev_node,"tags")[1]=="photo":
                    break
                if prev_node and tree.item(prev_node,"tags")[1]=="category":
                    # prev_node=self.select_from_category(prev_node)
                    while tree.item(prev_node, "tags")[1] =="category":
                        prev_node = tree.get_children(prev_node)[-1]
                    break
                parent_node = tree.parent(parent_node)
        if not prev_node:
            # 未找到上一张图片，重新播放最后一张图片
            prev_node = tree.get_children("")[-1]
            while tree.item(prev_node, "tags")[1] != "photo":
                prev_node = tree.get_children(prev_node)[-1]

        if prev_node:
            # print(tree.item(prev_node,"tags"))
            file_path = tree.item(prev_node, "tags")[0]
            image = Image.open(file_path)
            photo = ImageTk.PhotoImage(image)
            self.label.configure(image=photo)
            self.label.image = photo
            self.current_Node = prev_node
            self.current_image = image
            def resize_image(event):
                self.window.after(0, self.resize_image_label, event, self.label, image)
            self.label.bind("<Configure>", resize_image)
    def auto_play(self):
        # 自动播放图片
        if self.playing:
            # 如果已经在自动播放，停止自动播放
            self.playing = False
            self.play_button.config(text="自动播放")
            if self.timer_id:
                self.root.after_cancel(self.timer_id)  # 取消之前的定时器
        else:
            # 如果不在自动播放，开始自动播放
            self.playing = True
            self.play_button.config(text="停止播放")
            self.time=float(time_entry.get())
            self.timer_id = self.root.after(int(self.time * 1000), self.auto_play_next)  # 调用自动播放下一张图片
    def auto_play_next(self):
        # 自动播放下一张图片
        if self.playing:
            self.play_next_image()
            self.timer_id = self.root.after(int(self.time * 1000), self.auto_play_next)  # 继续调用自动播放下一张图片

    @staticmethod
    def resize_image_label(event, label, image):
        """
        在窗口尺寸变化时，重新调整图片大小以保持比例
        """
        new_width = event.width*0.9
        new_height = event.height*0.9

        # 按比例缩放图像以适应新窗口大小
        width_ratio = new_width / image.width
        height_ratio = new_height / image.height
        ratio = min(width_ratio, height_ratio)

        new_image_width = int(image.width * ratio)
        new_image_height = int(image.height * ratio)

        new_image = image.resize((new_image_width, new_image_height), Image.LANCZOS)
        new_photo = ImageTk.PhotoImage(new_image)

        label.configure(image=new_photo)
        label.image = new_photo

def on_tree_double_click(event):

    if tree.parent(selected_node) == "":
        return
    item_data = tree.item(selected_node, "tags")
    # print(item_data)
    node_type=item_data[1]
    if node_type=="photo" or node_type=="file":
        filepath=item_data[0]
        # show_image(filepath)
        Simg=ShowImage(root)
        Simg.current_Node=selected_node
        Simg.show_image(filepath) 


# 创建主窗口
root = tk.Tk()
root.title("Image File Search")

# 设置网格布局权重
root.grid_columnconfigure(1, weight=1)

# 添加控件
# 创建一个标签用于显示目录路径
label_path = tk.Label(root, text="文件目录:")
label_path.grid(row=0, column=0, padx=5, pady=5, sticky="e")

# 创建一个输入框用于输入或选择目录路径
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# 创建一个“浏览”按钮，用于选择目录
button_browse = tk.Button(root, text="浏览", command=browse_directory)
button_browse.grid(row=0, column=2, padx=5, pady=5)

# 创建一个标签用于显示分类信息
label_categories = tk.Label(root, text="目录:")
label_categories.grid(row=1, column=0, padx=5, pady=5, sticky="e")


# 创建一个树形视图用于展示分类
tree = ttk.Treeview(root)
tree.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
tree.bind("<<TreeviewSelect>>", on_select)
tree.bind("<Double-1>", on_tree_double_click)  # 绑定双击事件

# 创建一个垂直滚动条，与树形视图绑定
scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
scrollbar.grid(row=1, column=2, sticky="ns")
tree.config(yscrollcommand=scrollbar.set)


# 创建一个标签用于显示文件名
label_filename = tk.Label(root, text="所在类别下文件名:")
label_filename.grid(row=2, column=0, padx=5, pady=5, sticky="e")

# 创建一个输入框用于输入文件名
entry_filename = tk.Entry(root, width=50)
entry_filename.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

# 创建一个按钮，用于执行搜索操作
button_search = tk.Button(root, text="局部搜索", command=search)
button_search.grid(row=2, column=2, padx=5, pady=5, sticky="e")

# 创建一个标签用于显示分类信息
label_filename = tk.Label(root, text="类别:")
label_filename.grid(row=3, column=0, padx=5, pady=5, sticky="e")

# 创建一个变量，用于存储选中的类别属于哪个树节点
selected_node=tree.insert("", "end")

# 创建一个变量，用于存储选中的分类信息，并创建一个标签显示该信息
selected_category = tk.StringVar()
selected_category.set("")
label_selected_category = tk.Label(root, textvariable=selected_category)
label_selected_category.grid(row=3, column=1, padx=5, pady=5, sticky="ew")


# 创建一个标签用于显示图片格式
label_image_format = tk.Label(root, text="图片格式:")
label_image_format.grid(row=4, column=0, padx=5, pady=5, sticky="e")

# 创建一个输入框用于输入图片格式
entry_image_format = tk.Entry(root, width=10)
entry_image_format.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
entry_image_format.insert(0, DEFAULT_IMAGE_FORMAT)

# 创建一个按钮，用于更新图片格式
button_update_format = tk.Button(root, text="更新", command=update_image_format)
button_update_format.grid(row=4, column=2, padx=5, pady=5)

# 创建一个标签用于搜索功能
label_search = tk.Label(root, text="搜索栏:")
label_search.grid(row=5, column=0, padx=5, pady=5, sticky="e")

# 创建一个输入框，用于输入全局搜索关键词
entry_global_search = tk.Entry(root, width=50)
entry_global_search.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

# 创建一个按钮，用于执行全局搜索
button_global_search = tk.Button(root, text="全局搜索", command=global_search)
button_global_search.grid(row=5, column=2, padx=5, pady=5)

time_label = tk.Label(root, text="时间间隔（秒）:")
time_label.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
time_entry = tk.Entry(root,width=50)
time_entry.insert(0, "2")  # 默认时间间隔为2秒
time_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

# 显示注意事项
messagebox.showinfo("注意事项",f"请按照以下格式输入图片名称: 类别1-类别2-...-类别n-图片名称\n例如: cat-dog-1"+DEFAULT_IMAGE_FORMAT+"\n图片格式默认为"+DEFAULT_IMAGE_FORMAT+"\n请先选择文件目录，再进行搜索操作。\n目录中双击图片或图片所在路径即可查看图片。")


# 运行主循环
root.mainloop()