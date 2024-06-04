import json
import os

# 默认配置
DEFAULT_CONFIG = {
    "window_size": [800, 600],
    "image_formats": [".png",".jpg",".svg",".jpeg",".bmp",".gif",".tiff"],
    "default_path": "images",
    "deault_visual_path": "visual_images",
    "elements_translation": {"SIC":'海冰密集度',"SIT":'海冰厚度',"SIE":'海冰范围',"SIV":'海冰体积','SID':'海冰流速',"SIA": "海冰面积"},
    "Name_rule":'要素名称_年份_月份_日期',
}

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        if not self.check():
            self.config = DEFAULT_CONFIG
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
            f.write("# 请不要修改本文件，如需修改请按照格式增改\n")
            f.write(json.dumps(self.config, indent=4, ensure_ascii=False))

    def check(self):
        # 检查配置项是否存在
        return DEFAULT_CONFIG.keys() == self.config.keys()
    
    def get(self, key):
        # 获取配置项的值
        return self.config.get(key)

    def set(self, key, value):
        # 设置配置项的值
        self.config[key] = value
