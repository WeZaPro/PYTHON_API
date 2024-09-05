import torch

# โหลดโมเดล YOLOv5 ที่ฝึกอบรมเอง
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./custom_model/best.pt')

# ดูชื่อคลาสจากโมเดล
class_names = model.names
print(class_names)