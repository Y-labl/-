import tkinter as tk
from PIL import ImageGrab, Image
import sys

class ColorPicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('取色工具 - 点击晶石取色，右键结束')
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='black')
        
        self.colors = []
        self.label = tk.Label(self.root, text='左键点击晶石取色，右键结束', 
                              font=('Arial', 20), bg='black', fg='white')
        self.label.pack(pady=20)
        
        self.info = tk.Label(self.root, text='', font=('Arial', 14), bg='black', fg='yellow')
        self.info.pack()
        
        self.root.bind('<Button-1>', self.on_click)
        self.root.bind('<Button-3>', self.on_done)
        
        # Take initial screenshot
        self.screenshot = ImageGrab.grab()
        
    def on_click(self, event):
        x, y = event.x_root, event.y_root
        try:
            px = self.screenshot.getpixel((x, y))
            r, g, b = px[0], px[1], px[2]
            self.colors.append((x, y, r, g, b))
            text = f'#{len(self.colors)}: ({x},{y}) RGB({r},{g},{b}) hex=#{r:02X}{g:02X}{b:02X}'
            self.info.config(text=text)
            print(text)
        except:
            pass
    
    def on_done(self, event):
        self.root.destroy()
        if self.colors:
            print('\n=== 多点找色数据 ===')
            print('points = [')
            for x, y, r, g, b in self.colors:
                print(f'    (\"{r:02X}{g:02X}{b:02X}\", {x}, {y}),')
            print(']')
        sys.exit(0)

app = ColorPicker()
app.root.mainloop()
