
import numpy as np
from PyQt5.QtCore import QPoint

class const:
    ACTION_DOWN = 0
    ACTION_UP = 1
    ACTION_MOVE = 2

class Client:
    def __init__(self, device_id, bitrate=8000000, max_fps=10, max_size=800):
        self.device_id = device_id
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.max_size = max_size
        self.alive = False
        self.last_frame = np.zeros((448, 800, 3), dtype=np.uint8)
        self.resolution = (800, 448)
        self.control = Control()
    
    def start(self, threaded=True):
        self.alive = True
    
    def stop(self):
        self.alive = False

class Control:
    def touch(self, x, y, action=const.ACTION_DOWN):
        pass
