class Config:
    # 窗口配置
    WINDOW_TITLE = "Phone-4HDVB23218001313"

    # 图像识别配置
    MAX_ATTEMPTS = 5
    CONFIDENCE_THRESHOLD = 0.5

    # 模板搜索区域（可选，用于提速）
    # - key: Config.TEMPLATES 的键（如 "EXCHANGE"/"BUY"/"JINGSHI"）
    # - value:
    #   - (x, y, w, h) 且全为 0~1 的 float：表示相对截图宽高的比例区域
    #   - (x, y, w, h) 含 int：表示像素区域（相对窗口截图左上角）
    #
    # 默认不限制（None/缺省），会在整张截图上做 matchTemplate，最耗时。
    TEMPLATE_SEARCH_REGIONS = {}

    # 操作延迟配置（优化为极速模式）
    CLICK_DELAY = 0.01
    WINDOW_WAIT_DELAY = 0.05

    # 调试配置
    DEBUG_SAVE_IMAGES = False

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
