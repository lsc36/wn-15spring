import cv2
import numpy as np
import time

H = 1080
W = 1920
CH = 720
CW = 1600
LOCATE_SIZE = 140
PAD_H = (H - (LOCATE_SIZE / 7 * 8) * 2 - CH) / 2
PAD_W = (W - (LOCATE_SIZE / 7 * 8) * 2 - CW) / 2
CPAD_H = PAD_H + LOCATE_SIZE / 7 * 8
CPAD_W = PAD_W + LOCATE_SIZE / 7 * 8

O_FPS = 30
T_FPS = 60

DETECT_THS = 2000
prev_detect_locater = None
def detect_fix(sframe):
    global prev_detect_locater

    frame = cv2.Canny(sframe,200,300)
    _,conto,hier = cv2.findContours(frame.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    hier = hier[0]

    hierlog = {}
    for idx,h in enumerate(hier):
        parent = h[3]
        if parent == -1:
            hierlog[idx] = 1
        else:
            hierlog[idx] = hierlog[parent] + 1

    poss = set()
    for idx,deep in hierlog.items():
        if deep < 3 or deep > 6:
            continue

        coidx = idx
        area = []
        pos = None
        while coidx != -1:
            co = conto[coidx][:,0,:]
            a = cv2.contourArea(co)
            m = cv2.moments(co)
            if a < DETECT_THS:
                pos = None
                break
            area.append(a)
            pos = (m['m10'] / m['m00'],m['m01'] / m['m00'])
            coidx = hier[coidx][3]

        if pos is None:
            continue

        area.sort()
        mark = 0
        ra = area[0]
        for rb in area[1:]:
            r = rb / ra
            if r > 1.8 and r < 2.8:
                mark += 1
            ra = rb

        if mark == 2:
            poss.add(pos)

    locater = list(poss)
    if len(locater) > 4:
        c = cv2.convexHull(np.array(locater,dtype = np.float32),clockwise = True,returnPoints = False)[:,0]
        locater = list(map(lambda x: x[1],filter(lambda x: x[0] in c,enumerate(locater))))
        print(locater)

    if len(locater) < 3:
        if prev_detect_locater is None:
            return None

        locater = prev_detect_locater
    elif len(locater) == 3:
        if prev_detect_locater is None:
            return None

        dis = 0
        sp = None
        for p in prev_detect_locater:
            tmp = 0
            for v in locater:
                tmp += (p[0] - v[0]) ** 2 + (p[1] - v[1]) ** 2
            if tmp > dis:
                dis = tmp
                sp = p
        locater.append(sp)

    locater = sorted(locater,key = lambda x: x[0])
    l = sorted(locater[:2],key = lambda x: x[1])
    r = sorted(locater[2:],key = lambda x: x[1])
    locater[0] = l[0]
    locater[1] = r[0]
    locater[2] = r[1]
    locater[3] = l[1]
    prev_detect_locater = locater

    mat = cv2.getPerspectiveTransform(
            np.array(locater,dtype = np.float32),
            np.array([
                [PAD_W + LOCATE_SIZE / 2,PAD_H + LOCATE_SIZE / 2],
                [W - PAD_W - LOCATE_SIZE / 2,PAD_H + LOCATE_SIZE / 2],
                [W - PAD_W - LOCATE_SIZE / 2,H - PAD_H - LOCATE_SIZE / 2],
                [PAD_W + LOCATE_SIZE / 2,H - PAD_H - LOCATE_SIZE / 2]],dtype = np.float32))
    return cv2.warpPerspective(sframe,mat,(W,H))

invc = cv2.VideoCapture('VID_20150618_023812.mp4')
fourcc = cv2.VideoWriter_fourcc(*'X264')
fixc = cv2.VideoWriter('fix.avi',fourcc,30,(CW,CH))

index = 0
while invc.isOpened():
    _,sframe = invc.read()
    if sframe is None:
        break
    print(index)
    index += 1

    fframe = detect_fix(sframe)
    fixc.write(fframe[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W])
    #cv2.waitKey(0)

fixc.release()
cv2.destroyAllWindows()
