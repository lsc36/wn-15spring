import numpy as np
import cv2
import fftutils

syms = fftutils.gensymbol(23,fftutils.SYMLEN,fftutils.SYMNUM)

invc = cv2.VideoCapture('/home/user/fin/MVI_9132.MOV')

index = 0
aframe = None
chs = None

datas = []
while True:
    print(index)
    index += 1
    _,sframe = invc.read()
    if sframe is None:
        break

    if index < 20:
        continue

    off = (sframe.shape[1] - 720) // 2
    frame = sframe[:720,off:720 + off]
    cv2.imshow('i',frame)

    bri = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)[:,:,2]
    if aframe is None:
        aframe = bri.astype(np.float)
        continue
    cv2.imshow('b',bri)

    bframe = bri.astype(np.float)
    cframe = (aframe - bframe) / 2
    aframe = bframe
    cv2.imshow('c',(cframe + 128).astype(np.uint8))

    if chs is None:
        chs = fftutils.detch(syms[0],cframe)
        if chs is None:
            continue

    data = []
    hints = []
    for idx,ch in enumerate(chs):
        print('detpat %d'%idx)
        sidx,cor = fftutils.detpat(syms,cframe,ch)
        hframe = cframe
        if cor < 0.7:
            print('second try')
            tsidx,tcor = fftutils.detpat(syms,bframe,ch)   
            if tcor > 0.6 and tcor > cor:
                sidx = tsidx
                hframe = bframe

        data.append(sidx)
        hints.append((hframe,syms[sidx],ch))
 
    tchs = fftutils.optch(hints)
    if tchs is not None:
        nchs = tchs

    print(data)
    datas.append(data[0] * 16 + data[1])

    cv2.waitKey(1)

invc.release()
print(datas)

SEQSHIFT = 2
SEQMASK = (1 << SEQSHIFT) - 1
def fixseq(b):
    seq = [0,1,2,3] * 64
    dp = np.full((257,257),-1)
    pa = np.full((257,257),-1)
    l = len(b)

    for i in range(l + 1):
        dp[i][0] = i
        dp[0][i] = i
    for i in range(1,l + 1):
        for j in range(1,l + 1):
            pa[i][j] = 0
            dp[i][j] = dp[i - 1][j] + 1
            if (dp[i][j - 1] + 1) < dp[i][j]:
                pa[i][j] = 1
                dp[i][j] = dp[i][j - 1] + 1
            if (b[i - 1] & SEQMASK) == seq[j - 1] and dp[i - 1][j - 1] < dp[i][j]:
                pa[i][j] = 2
                dp[i][j] = dp[i - 1][j - 1]

    u,v = l,l
    ps = []
    while True:
        if pa[u][v] == 0:
            u -= 1
        elif pa[u][v] == 1:
            v -= 1
        elif pa[u][v] == 2:
            ps.append((u - 1,v - 1))
            u -= 1
            v -= 1
        else:
            break

    ps.reverse()

    lpv = 0
    fb = []
    for pu,pv in ps:
        fb.extend([-1] * (pv - lpv - 1))
        fb.append(b[pu] >> SEQSHIFT)
        lpv = pv
    
    if len(fb) % 16 != 0:
        fb.extend([-1] * (16 - len(fb) % 16))
    return fb

lseq = None
seg = []
fseq = []
for idx,x in enumerate(datas):
    s = x & SEQMASK
    v = x >> SEQSHIFT
    if lseq == s:
        continue
    lseq = s
    if v == 0:
        fseq.extend(fixseq(seg))
        seg = []
    seg.append(x)

odatas = [0,1,2,3,4,5,6,7,8,9,30,31,32,43,54,61] * 1000
err = 0
for u,v in zip(fseq,odatas):
    if u != v:
        err += 1
print(err,len(fseq))
