import numpy as np
import cv2
from reedsolo import RSCodec

B = 120
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

def gs(X,row_vecs = True,norm = True):
    if not row_vecs:
        X = X.T
    Y = X[0:1,:].copy()
    for i in range(1,X.shape[0]):
        proj = np.diag((X[i,:].dot(Y.T) / np.linalg.norm(Y,axis = 1) ** 2).flat).dot(Y)
        Y = np.vstack((Y, X[i,:] - proj.sum(0)))
    if norm:
        Y = np.diag(1 / np.linalg.norm(Y,axis = 1)).dot(Y)
    if row_vecs:
        return Y
    else:
        return Y.T

def gensymbol(seed,size,num):
    np.random.seed(seed)
    vecs = []
    for idx in range(num):
        #vec = list(map(lambda x: np.random.uniform(0.0,600000),range(size)))
        while True:
            vec = list(map(lambda x: np.random.uniform(0.0,300000),range(size)))
            flag = False
            for v in vecs:
                if np.corrcoef(vec,v)[0,1] > 0.1:
                    flag = True
                    break
            if not flag:
                break
        print(idx)
        vecs.append(vec)
    return vecs

def genpat(pattern):
    d = np.zeros((B,B),dtype = np.float)
    index = 0
    for y in range(B):
        for x in range(B):
            if (x + y) >= 0 and (x + y) < 30:
                d[y,x] = pattern[index]
                index += 1
    return d

def gends(seed):
    np.random.seed(seed)
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
    return ds

def genkframe(seed):
    np.random.seed(seed)
    keys = []
    for j in range(256):
        v = []
        for i in range((1 + 30) * 30 // 2):
            v.append(np.random.normal(0,10000))
        keys.append(v)
    keys = np.array(keys)
    keys = gs(keys) * 1000
    kframes = []
    for key in keys:
        print(np.max(key))
        print(np.min(key))
        d = genpat(key)
        kframe = cv2.dct(d,cv2.DCT_INVERSE)
        kframes.append(kframe)
        print(np.max(kframe))
        print(np.min(kframe))
        #cv2.imshow('d',(kframe + 128).astype('uint8'))
        #cv2.waitKey(0)
    return kframes

def extract(sframe,kframes):
    data = []
    for y in range(0,CH,B):
        for x in range(0,CW,B):
            ma = 0
            maidx = 0
            e = sframe[y:y + B,x:x + B]
            for idx,d in enumerate(kframes):
                v = abs(np.sum(d * e))
                if v > ma:
                    ma = v
                    maidx = idx
            data.append(maidx)

    return bytearray(data)

def modul(msg,size):
    rsc = RSCodec(size - len(msg))
    data = rsc.encode(msg)

    return data
    '''
    idx = 0
    for c in data:
        s = bin(c)[2:].rjust(8,'0')[::-1]
        for x in s:
            ret[idx] = (ret[idx] << 1) | int(x)
            idx = (idx + 7) % size

    return ret
    '''
def demodul(data,size):
    assert(size % 7 != 0)

    '''
    ret = bytearray(size)
    ndata = bytearray(data)
    idx = (-7) % size
    for i in range(size - 1,-1,-1):
        for j in range(8):
            ret[i] = (ret[i] << 1) | (ndata[idx] & 1)
            ndata[idx] = (ndata[idx] >> 1)
            idx = (idx - 7) % size
    '''

    rsc = RSCodec(size - 14)
    try:
        ret = rsc.decode(data)
    except:
        ret = None

    return ret
