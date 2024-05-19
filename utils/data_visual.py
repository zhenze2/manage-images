# draw_pic
from PyQt5.QtWidgets import  QMainWindow,QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QGridLayout
import numpy as np
import pandas as pd

import pyqtgraph as pg

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