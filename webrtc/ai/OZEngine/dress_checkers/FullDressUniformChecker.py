import sys
import numpy as np
import re
from OZEngine.dress_classifier import classification2
from lib.utils import sortContoursByArea, getVertexCnt, getContourCenterPosition, getRectCenterPosition, isPointInBox
from lib.defines import *
from lib.ocr import OCR
from lib.utils import plt_imshow

# (동)정복 검사


class FullDressUniformChecker():
    def __init__(self):
        # hyperparameter
        self.uniform_filter = {'lower': (12, 0, 0), 'upper': (197, 255, 116)}
        self.anchor_filter = {'lower': (20, 100, 100), 'upper': (30, 255, 255)}
        self.classes_filter = {
            'lower': (140, 120, 50), 'upper': (190, 255, 255)}
        self.mahura_filter = {
            'lower': (140, 120, 50), 'upper': (190, 255, 255)}

        self.name_tag_pattern = re.compile('[가-힣]+')

    def name_tag_filter(self, string):
        print('str', string)
        filtered_list = self.name_tag_pattern.findall(string)
        res_string = ''.join(filtered_list)
        return res_string

    def getMaskedContours(self, img=None, hsv_img=None, morph=None, kmeans=None, kind=None, sort=False):
        if hsv_img is None:
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if kind == 'uniform':
            lower, upper = self.uniform_filter['lower'], self.uniform_filter['upper']
        elif kind == 'classes':
            lower, upper = self.classes_filter['lower'], self.classes_filter['upper']
        elif kind == 'anchor':
            lower, upper = self.anchor_filter['lower'], self.anchor_filter['upper']
        else:
            pass

        mask = cv2.inRange(hsv_img, lower, upper)

        if kmeans:
            img_s = classification2(img)
            plt_imshow(['origin', 's'], [img, img_s])
            img = classification2(img)

        if morph == 'erode':
            kernel = np.ones((3, 3), np.uint8)
            org_mask = mask.copy()

            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 2))
            mask = cv2.erode(org_mask, k, iterations=2)

            plt_imshow(['org_mask', 'maskk', 'm2'], [org_mask, mask])

        masked_img = cv2.bitwise_and(img, img, mask=mask)

        if sort:
            contours, hierarchy = cv2.findContours(
                mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            sorted_contours, sorted_hierarchy = sortContoursByArea(
                contours, hierarchy)
            return sorted_contours, sorted_hierarchy, masked_img
        else:
            contours, _ = cv2.findContours(
                mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            return contours, masked_img

    def getName(self, img, contours, hierarchy):
        h, w = img.shape[:2]
        shirt_contour, res_box_position, res_content = None, None, None
        ocr_list = OCR(img)

        # 이름표
        shirt_node = None
        for i, (contour, lev) in enumerate(zip(contours, hierarchy)):
            cur_node, next_node, prev_node, first_child, parent = lev
            if i == 0:  # 정복
                img2 = img.copy()
                shirt_contour = contour
                cv2.drawContours(img2, [contour], -1, Color.RED, -1)
                plt_imshow('img2', img2)
                shirt_node = cur_node
                continue

            # 정복 영영 안쪽 && 모서리가 4~5 && 크기가 {hyperParameter} 이상 => (이름표)
            # 이름표 체크
            if not res_content and parent == shirt_node and 4 <= getVertexCnt(contour) <= 10 and cv2.contourArea(contour) > 300:
                center_p = getContourCenterPosition(contour)
                max_xy, min_xy = np.max(contour, axis=0)[
                    0], np.min(contour, axis=0)[0]

                # 이름표 체크
                if center_p[0] < (w//2):
                    name_chrs = []

                    sorted_orc_list = sorted(
                        ocr_list, key=lambda ocr_res: ocr_res['boxes'][0][0])
                    for ocr_res in sorted_orc_list:
                        ocr_str, ocr_box = ocr_res['recognition_words'][0], ocr_res['boxes']
                        ocr_str = self.name_tag_filter(ocr_str)
                        p1, p2, p3, p4 = ocr_box
                        (x1, y1), (x2, y2) = p1, p3
                        if x2 < w//2:
                            roi = img[y1:y2, x1:x2]

                            ocr_center_xy = getRectCenterPosition(ocr_box)
                            if isPointInBox(ocr_center_xy, (min_xy, max_xy)):
                                name_chrs.append(ocr_str)
                                cv2.rectangle(img, p1, p3, Color.GREEN, 3)
                            else:
                                pass
                        else:
                            break
                    res_box_position, res_content = cv2.boundingRect(
                        contour), ''.join(name_chrs)

        return cv2.boundingRect(shirt_contour), res_box_position, res_content

    def getClasses(self, masked_img, contours, hierarchy):
        h, w = masked_img.shape[:2]
        res_box_position, res_content, small_mask = None, None, None

        box_position = None

        # 계급장 체크
        for contour in contours:
            if res_content:
                break
            if cv2.contourArea(contour) > 300:
                center_p = getContourCenterPosition(contour)
                if center_p[0] < (w//2):
                    box_position = cv2.boundingRect(contour)
                    x, y, w, h = box_position
                    roi = masked_img[y:y+h, x:x+w]
                    small_contours, small_mask = self.getMaskedContours(
                        img=roi, kind='classes')

                    classes_n = 0
                    for small_contour in small_contours:
                        if 10 < cv2.contourArea(small_contour):
                            classes_n += 1
                            cv2.drawContours(
                                small_mask, [small_contour], 0, Color.BLUE, 1)

                    if 1 <= classes_n <= 4:
                        res_box_position = box_position
                        res_content = Classes.dic[classes_n]

        return res_box_position, res_content, small_mask

    def getAnchor(self, contours, hierarchy):
        res_box_position, res_content = None, None

        # 계급장 체크
        for contour in contours:
            if cv2.contourArea(contour) > 100:
                center_p = getContourCenterPosition(contour)
                res_box_position = cv2.boundingRect(contour)
                res_content = True
                break
        return res_box_position, res_content

    def getMahura(self, contours, hierarchy):
        res_box_position, res_content = None, None
        for contour in contours:
            if cv2.contourArea(contour) > 300:
                center_p = getContourCenterPosition(contour)
                if not res_content:
                    res_box_position = cv2.boundingRect(contour)
                    res_content = True

        return res_box_position, res_content

    def checkUniform(self, org_img):
        img = org_img
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        box_position_dic = {}
        component_dic = {}
        masked_img_dic = {}

        # 이름표 체크
        name = 'name'
        contours, sorted_hierarchy, masked_img_dic[name] = self.getMaskedContours(
            img=img, hsv_img=hsv_img, kind='uniform', sort=True)
        box_position, component, masked_img = self.getName(
            img, contours, sorted_hierarchy)
        box_position_dic['shirt'] = box_position
        box_position_dic[name] = component
        component_dic[name] = masked_img

        # 네카치프 / 네카치프링 체크
        name = 'anchor'
        contours, masked_img_dic[name] = self.getMaskedContours(
            img=img, hsv_img=hsv_img, kind=name)
        box_position, component = self.getAnchor(contours, None)
        box_position_dic[name] = box_position
        component_dic[name] = component

        # 계급장 체크
        name = 'classes'
        contours, masked_img_dic[name] = self.getMaskedContours(
            img=img, hsv_img=hsv_img, kind=name)
        box_position, component, masked_img = self.getClasses(
            img, contours, None)
        box_position_dic[name] = box_position
        component_dic[name] = component
        masked_img_dic[name] = masked_img

        # 마후라 체크
        # name = 'mahura'
        # contours = self.getMaskedContours(
        #     img=img, hsv_img=hsv_img, kind=name, sort=False)
        # box_position_dic[name], component_dic[name] = self.getMahura(
        #     img, contours, None)

        return component_dic, box_position_dic, masked_img_dic
