from lib.utils import *
from lib.defines import *
from lib.ocr import OCR, draw_rectangle


# 샘브레이 검사
class NavyServiceUniformChecker():
    def __init__(self):
        # hyperparameter
        self.uniform_filter = {'lower': (30, 20, 0), 'upper': (255, 255, 255)}
        self.classes_filter = {
            'lower': (0, 150, 90), 'upper': (255, 255, 255)}

        self.debug_mode = False

    def getMaskedContours(self, img=None, hsv_img=None, kind=None, sort=True):
        if kind == 'uniform':
            lower, upper = self.uniform_filter['lower'], self.uniform_filter['upper']
        elif kind == 'classes':
            lower, upper = self.classes_filter['lower'], self.classes_filter['upper']
        else:
            pass

        mask = cv2.inRange(hsv_img, lower, upper)
        masked_img = cv2.bitwise_and(img, img, mask=mask)

        if sort:
            contours, hierarchy = cv2.findContours(
                mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            sorted_contours, sorted_hierarchy = sortContoursByArea(
                contours, hierarchy)
            return sorted_contours, sorted_hierarchy
        else:
            contours, _ = cv2.findContours(
                mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            return contours

    def getName(self, contour, ocr_list):
        max_xy, min_xy = np.max(contour, axis=0)[
            0], np.min(contour, axis=0)[0]

        name_chrs = []
        for ocr_res in ocr_list:
            print('ocr res:', ocr_res)
            ocr_str, ocr_box = ocr_res['recognition_words'], ocr_res['boxes']
            ocr_center_xy = getRectCenterPosition(ocr_box)
            if isPointInBox(ocr_center_xy, (min_xy, max_xy)):
                name_chrs.append(ocr_str[0])
            else:
                pass

        return contour, ''.join(name_chrs)

    def getClasses(self, img, hsv_img, contour):
        contours = self.getMaskedContours(
            img=img, hsv_img=hsv_img, kind='classes', sort=False)

        x, y, w, h = cv2.boundingRect(contour)
        roi = img[y:y+h, x:x+w]
        hsv_roi = hsv_img[y:y+h, x: x+w]

        classes_n = 0
        for contour in contours:
            if 10 < cv2.contourArea(contour):
                classes_n += 1

        if 1 <= classes_n <= 4:
            return contour, Classes.dic[classes_n]
        else:
            return None, None

    def checkUniform(self, org_img):
        img = org_img
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, w = img.shape[: 2]

        # 샘당 filter
        contours, hierarchy = self.getMaskedContours(
            img=img, hsv_img=hsv_img, kind='uniform')

        # 이름표 OCR
        ocr_list = OCR(img)

        contour_dic = {}
        component_dic = {}
        debug_img = {}

        # 이름표, 계급장 체크
        for i, (contour, lev) in enumerate(zip(contours, hierarchy)):
            cur_node, next_node, prev_node, first_child, parent = lev
            if i == 0:  # 셈브레이
                shirt_node = cur_node
                continue

            # 샘브레이 영영 안쪽 && 모서리가 4~5 && 크기가 {hyperParameter} 이상 => (이름표 or 계급장)
            # 이름표 또는 계급장
            if (not component_dic.get('name_tag') or not component_dic.get('class_tag')) and \
                    parent == shirt_node and \
                    3 <= getVertexCnt(contour) <= 10 and \
                    cv2.contourArea(contour) > 300:

                center_p = getContourCenterPosition(contour)

                # 이름표 체크
                name = 'name_tag'
                if center_p[0] < (w//2) and not component_dic.get(name):
                    contour_dic[name], component_dic[name] = self.getName(contour, ocr_list)

                # 계급장 체크
                elif center_p[0] > (w//2) and not component_dic.get('class_tag'):
                    contour_dic[name], component_dic[name] = self.getClasses(img, hsv_img, contour)

        # half_line_p1, half_line_p2 = (w//2, 0), (w//2, h)
        # cv2.line(img, half_line_p1, half_line_p2, Color.WHITE, 5)
        return component_dic, contour_dic, debug_img
