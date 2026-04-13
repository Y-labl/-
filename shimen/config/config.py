import os

class Config:
    """配置管理类"""
    # 游戏窗口标题
    WINDOW_TITLE = "梦幻西游 ONLINE - (福建2区[鼓浪屿] - °紫月べ清风[37279872])"
    
    # 图像识别配置
    MAX_ATTEMPTS = 50  # 最大尝试次数
    CONFIDENCE = 0.7  # 匹配阈值
    RETRY_WAIT = 0.2  # 重试间隔时间(秒)
    
    # 目录配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATE_DIR = "templates"  # 模板图片目录
    
    # 模板图片路径
    TEMPLATES = {
        "SM": "sm.png",  # 师门传送口
        "SM_CHUANSONG": "smchuansongkou.png",  # 传送口
        "KDCS": "kdcs.png",  # 传送口
        "ZUOBIAO": "baotuzuobiao/zuobiao.png"  # 坐标
    }
    
    # 任务追踪区域配置
    TASK_TRACKING = {
        "LEFT": 650,  # 相对窗口左侧的偏移
        "TOP": 100,  # 相对窗口顶部的偏移
        "WIDTH": 150,  # 宽度
        "HEIGHT": 150  # 高度
    }
    
    @classmethod
    def get_template_path(cls, template_name):
        """获取模板图片路径"""
        if template_name in cls.TEMPLATES:
            return os.path.join(cls.BASE_DIR, cls.TEMPLATE_DIR, cls.TEMPLATES[template_name])
        return None
    
    @classmethod
    def update_window_title(cls, title):
        """更新窗口标题"""
        cls.WINDOW_TITLE = title
