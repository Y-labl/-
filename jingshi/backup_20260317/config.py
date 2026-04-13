class Config:
    # 窗口配置
    WINDOW_TITLE = "Phone-4HDVB23218001313"
    
    # 图像识别配置
    MAX_ATTEMPTS = 5
    CONFIDENCE_THRESHOLD = 0.5
    
    # 操作延迟配置
    CLICK_DELAY = 0.1
    WINDOW_WAIT_DELAY = 0.5
    
    # 模板路径
    TEMPLATES = {
        "EXCHANGE": "兑换.png",
        "JINGSHI": "晶石.png",
        "BUY": "购买.png"
    }
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
