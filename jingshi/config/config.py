class Config:
    # 窗口配置
    WINDOW_TITLE = "Phone-4HDVB23218001313"
    
    # 图像识别配置
    MAX_ATTEMPTS = 5
    CONFIDENCE_THRESHOLD = 0.5
    
    # 操作延迟配置（优化为极速模式）
    CLICK_DELAY = 0.01
    WINDOW_WAIT_DELAY = 0.05
    
    # 模板路径（与 exe 同目录或打包进 _MEIPASS 根目录）
    TEMPLATES = {
        "EXCHANGE": "兑换.png",
        "JINGSHI": "晶石.png",
        "BUY": "购买.png",
        "LEVEL_120": "120.png",  # 「只抢 120」时匹配等级文字用，需自行截图放入工程根目录
    }
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
