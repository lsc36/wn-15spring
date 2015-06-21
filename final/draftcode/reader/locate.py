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

DETECT_THS = 500
prev_detect_locater = None
def detect_fix(index,sframe):
    global prev_detect_locater

    frame = cv2.Canny(sframe,100,400)
    _,conto,hier = cv2.findContours(frame.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return None
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
        if deep != 6:
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

    print(locater)

    mat = cv2.getPerspectiveTransform(
            np.array(locater,dtype = np.float32),
            np.array([
                [PAD_W + LOCATE_SIZE / 2,PAD_H + LOCATE_SIZE / 2],
                [W - PAD_W - LOCATE_SIZE / 2,PAD_H + LOCATE_SIZE / 2],
                [W - PAD_W - LOCATE_SIZE / 2,H - PAD_H - LOCATE_SIZE / 2],
                [PAD_W + LOCATE_SIZE / 2,H - PAD_H - LOCATE_SIZE / 2]],dtype = np.float32))
    return cv2.warpPerspective(sframe,mat,(W,H))


chess_b = np.full((16,16),0)
chess_w = np.full((16,16),255)
chess = np.concatenate(
        [np.concatenate([chess_b,chess_w] * 16),np.concatenate([chess_w,chess_b] * 16)] * 16,
        axis = 1)
chess_inv = np.concatenate(
        [np.concatenate([chess_w,chess_b] * 16),np.concatenate([chess_b,chess_w] * 16)] * 16,
        axis = 1)

invc = cv2.VideoCapture('MOV_0024.MP4')
fps = invc.get(cv2.CAP_PROP_FPS)
print(fps)
fourcc = cv2.VideoWriter_fourcc(*'X264')
fixc = cv2.VideoWriter('fix.avi',fourcc,fps,(CW,CH))

index = 0
while invc.isOpened():
    #_,sframe = invc.read()
    #if sframe is None:
    #    break
    print(index)
    index += 1
    
    bframe = detect_fix(0,invc.read()[1])
    if bframe is None:
        continue

    bframe = bframe[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W].astype(np.uint8)
    bframe = cv2.cvtColor(bframe,cv2.COLOR_RGB2HSV)
    bframe = bframe[:512,:512,2]

    dcta = cv2.dct((chess - 128).astype(np.float))
    #dframe = (dct / np.max(dct) * 255).astype(np.uint8)
    dcta[0,0] = 0.0

    dctb = cv2.dct((bframe - 128).astype(np.float))
    #dct -= np.min(dct)
    #pframe = (dct / np.max(dct) * 255).astype(np.uint8)

    print(dcta)
    print(dctb)
    print(np.sum(dcta * dctb))

    cv2.imshow('x',bframe)
    cv2.waitKey(0)

    #bframe = cv2.adaptiveThreshold(bframe,200,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,17,0)

    aframe = bframe

    #fframe = detect_fix(index,sframe)
    #if fframe is None:
    #    continue

    #fixc.write(fframe[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W])

fixc.release()
cv2.destroyAllWindows()
