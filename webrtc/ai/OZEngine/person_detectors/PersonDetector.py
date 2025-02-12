import enum
import cv2
import numpy as np
from lib.utils import *
from lib.defines import Color
import os

if __file__:
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    WEIGHTS_PATH = os.path.join(cur_dir, 'refs/weights/yolov4.weights')
    CFG_PATH = os.path.join(cur_dir, 'refs/cfg/yolov4.cfg')
else:
    WEIGHTS_PATH = 'OZEngine/person_detectors/refs/weights/yolov4.weights'
    CFG_PATH = 'OZEngine/person_detectors/refs/cfg/yolov4.cfg'


class PersonDetector():
    def __init__(self, only_person=True):
        self.net = cv2.dnn.readNet(WEIGHTS_PATH, CFG_PATH)
        self.classes = []
        if only_person:
            self.classes = ['person']
        else:
            with open("OZEngine/person_detectors/names/coco_finetuned.names", "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i-1]
                              for i in self.net.getUnconnectedOutLayers()]
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))

    def detect(self, org_img):
        img = org_img
        height, width, channels = img.shape
        blob = cv2.dnn.blobFromImage(
            img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    # 좌표
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        # font = cv2.FONT_HERSHEY_PLAIN

        x, y, w, h = None, None, None, None
        for i, (box, class_id) in enumerate(zip(boxes, class_ids)):
            if i in indexes:
                if class_id > len(self.classes):
                    continue
                else:
                    x, y, w, h = box
                    break
        x = max(0, x)
        y = max(0, y)  
        return ((y,x), (y+h, x+w))
