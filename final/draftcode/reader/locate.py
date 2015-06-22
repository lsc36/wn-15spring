import cv2
import numpy as np
import time

H = 1080
W = 1920
CH = 720
CW = 1560
LOCATE_SIZE = 105
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

def get_alignblock(sframe):
    frame = cv2.Canny(sframe,100,400)
    _,conto,hier = cv2.findContours(frame.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return np.array([])
    pos = []
    for idx,h in enumerate(hier[0]):
        if h[3] != -1:
            continue
        co = conto[idx][:,0,:]
        a = cv2.contourArea(co)
        if a < 100:
            continue
        m = cv2.moments(co)
        pos.append((m['m10'] / m['m00'],m['m01'] / m['m00']))
    return np.array(pos)

def align(sframe):
    post = get_alignblock(sframe[PAD_H:PAD_H + LOCATE_SIZE,CPAD_W - LOCATE_SIZE / 8:W - CPAD_W + LOCATE_SIZE / 8])
    post += [PAD_H,CPAD_W - LOCATE_SIZE / 8]
    posb = get_alignblock(sframe[H - PAD_H - LOCATE_SIZE:H - PAD_H,CPAD_W - LOCATE_SIZE / 8:W - CPAD_W + LOCATE_SIZE / 8])
    posb += [H - PAD_H - LOCATE_SIZE,CPAD_W - LOCATE_SIZE / 8]
    post = sorted(post,key = lambda x: x[0])
    posb = sorted(posb,key = lambda x: x[0])

def gs(X,row_vecs = True,norm = True):
    if not row_vecs:
        X = X.T
    Y = X[0:1,:].copy()
    for i in range(1, X.shape[0]):
        proj = np.diag((X[i,:].dot(Y.T)/np.linalg.norm(Y,axis=1)**2).flat).dot(Y)
        Y = np.vstack((Y, X[i,:] - proj.sum(0)))
    if norm:
        Y = np.diag(1/np.linalg.norm(Y,axis=1)).dot(Y)
    if row_vecs:
        return Y
    else:
        return Y.T

def genpat(pattern):
    d = np.zeros((120,120),dtype = np.float)
    index = 0
    for y in range(120):
        for x in range(120):
            if (x + y) >= 0 and (x + y) < 30:
                d[y,x] = pattern[index]
                index += 1
    return d

def extract(sframe):
    data = []
    for y in range(0,CH,120):
        for x in range(0,CW,120):
            ma = 0
            maidx = 0
            e = cv2.dct(sframe[y:y + 120,x:x + 120])
            for idx,d in enumerate(ds):
                v = abs(np.sum(d * e))
                if v > ma:
                    ma = v
                    maidx = idx
            data.append(maidx)
    return data

invc = cv2.VideoCapture('MVI_9072.MOV')
fps = invc.get(cv2.CAP_PROP_FPS)
print(fps)
fourcc = cv2.VideoWriter_fourcc(*'X264')
fixc = cv2.VideoWriter('fix.avi',fourcc,fps,(CW,CH))
    
'''
chess_b = np.full((16,16),0)
chess_w = np.full((16,16),255)
chess = np.concatenate(
        [np.concatenate([chess_b,chess_w] * 16),np.concatenate([chess_w,chess_b] * 16)] * 16,
        axis = 1)
chess_inv = np.concatenate(
        [np.concatenate([chess_w,chess_b] * 16),np.concatenate([chess_b,chess_w] * 16)] * 16,
        axis = 1)
'''

np.random.seed(23)
keys = []
for j in range(256):
    v = []
    for i in range((1 + 30) * 30 // 2):
        v.append(np.random.normal(0,10000))
    keys.append(v)
keys = np.array(keys)
keys = gs(keys) * 1000
ds = []
for key in keys:
    ds.append(genpat(key))

index = 0
aframe = None
while invc.isOpened():
    #_,sframe = invc.read()
    #if sframe is None:
    #    break
    print(index)
    index += 1
    
    bframe = detect_fix(0,invc.read()[1])
    if bframe is None:
        continue
    #align(bframe)

    bframe = bframe.astype(np.uint8)
    bframe = bframe[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W]
    bframe = cv2.cvtColor(bframe,cv2.COLOR_RGB2HSV)
    bframe = bframe[:,:,2]
    print(bframe.shape)

    if aframe is not None:
        cframe = (aframe.astype(np.float) + bframe.astype(np.float)) / 2.0
        cframe = (bframe.astype(float) - cframe)

        print(extract(cframe))
        
        cv2.imshow('x',(cframe + 128).astype(np.uint8))
        cv2.waitKey(0)

    aframe = bframe

fixc.release()
cv2.destroyAllWindows()
