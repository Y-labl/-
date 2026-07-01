# -*- coding: utf-8 -*-
import os

doc = """

(the content will be written separately)

"""

path = r"D:\工作\新建文件夹\stoneclient\DOCUMENTATION.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"Written to {path}")
