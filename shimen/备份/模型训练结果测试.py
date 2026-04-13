from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np

app = Flask(__name__)
model = YOLO('runs/detect/train4/weights/best.pt')

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files['image']
    img = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_COLOR)
    results = model.predict(source=img)
    # 对results进行处理，转化为合适格式返回给前端
    return jsonify({'results': '处理后的结果信息'})

if __name__ == '__main__':
    app.run(debug=True)