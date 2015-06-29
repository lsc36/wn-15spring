import numpy as np
import cv2
import math
import utils

SYMLEN = 30
SYMNUM = 16

def genpos(radius,scale,theta = 0):
    sympos = list(map(lambda x: (
        radius * math.cos(x * np.pi / SYMLEN + theta),
        radius * math.sin(x * np.pi / SYMLEN + theta)
        ),range(SYMLEN)))
    sympos += list(map(lambda x: (-x[0],-x[1]),sympos))
    sympos = list(map(lambda x: (
        round(scale // 2 + x[0]),
        round(scale // 2 + x[1])),sympos))
    return sympos

def genpat(sym):
    scale = 512
    radius = (scale / 2) * 0.162
    #sympos = genpos(radius,scale)
    sympos = genpos(radius * 1.5,scale)
    sympos += genpos(radius * 2,scale)
    #sympos += genpos(radius * 2.5,scale)
    #sympos += genpos(radius * 3,scale)

    spt = np.zeros((scale,scale),dtype = np.complex)
    
    vec = []
    for i in range(3):
        tvec = list(map(lambda x: x * np.exp(1j * np.random.uniform(0,np.pi * 2)),sym))
        vec.extend(tvec)
        vec.extend(np.conj(tvec))

    for idx,v in enumerate(vec):
        spt[sympos[idx]] = v
    pat = np.round(np.real(np.fft.ifft2(np.fft.ifftshift(spt))))

    #cv2.imshow('x',spt.astype(np.uint8) + 128)
    #tmp = np.abs(np.fft.fftshift(np.fft.fft2(pat + 128)))
    #cv2.imshow('y',(np.log10(np.maximum(1,tmp)) * 20).astype(np.uint8))
    #cv2.waitKey(0)

    print(np.max(np.abs(pat)))
    assert(np.max(np.abs(pat)) > 20 and np.max(np.abs(pat)) < 100)
    return pat

def extendpat(pat,size):
    hr,wr = pat.shape
    wr = size[0] // wr
    hr = size[1] // hr
    return cv2.repeat(pat,hr,wr)

def detch(pat):
    paty,patx = pat.shape
    scale = patx

    spt = np.abs(np.fft.fftshift(np.fft.fft2(pat.astype(np.float))))
    spt = cv2.GaussianBlur(spt,(3,3),0)

    maxv = 0
    maxr = (0,0)
    for r in range(15,100):
        print('--%d--'%r)

        for theta in range(-90,90):
            sympos = genpos(r,scale,theta * np.pi / 180)
            vec = list(map(lambda x: spt[x],sympos))
            cor = np.corrcoef(syms[0] * 2,vec)[0,1]
            if cor > maxv:
                maxv = cor
                maxr = (r,theta)

    print(maxv)
    print(maxr)

    tmp = np.clip(spt / 1000,0,255).astype(np.uint8)
    cv2.circle(tmp,(scale // 2,scale // 2),maxr[0],(255,0,0))
    cv2.imshow('tmp%d'%patx,tmp)

    return maxr

def detpat(pat,radius,theta):
    paty,patx = pat.shape
    scale = patx

    spt = np.abs(np.fft.fftshift(np.fft.fft2(pat.astype(np.float))))
    spt = cv2.GaussianBlur(spt,(3,3),0)
    sympos = genpos(radius,scale,theta * np.pi / 180)

    vec = list(map(lambda x: spt[x],sympos))
    for sym in syms:
        cor = np.corrcoef(sym * 2,vec)[0,1]
        if cor > 0.1:
            print(cor)

if __name__ == '__main__':
    syms = utils.gensymbol(23,SYMLEN,SYMNUM)
    print(syms)

    pats = list(map(lambda x: extendpat(genpat(x),(1024,1024)),syms))
    cv2.imshow('dframe',pats[0].astype(np.uint8) + 128)
    cv2.waitKey(0)
    exit()

    #invc = cv2.VideoCapture('/home/user/Downloads/test.mkv')
    #invc = cv2.VideoCapture('/home/user/fin/MVI_9120.MOV')
    #for i in range(10):
    #    _,sframe = invc.read()
    #_,sframe = invc.read()
    sframe = cv2.imread('/home/user/Downloads/1908084_740428942732671_7684358515802468396_n.jpg')
    sframe = cv2.repeat(sframe,5,5)
    off = 0
    frame = sframe[:1024,off:1024 + off]
    
    #frame = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)
    #np.clip(frame[:,:,2] * 0.8 + 25.6 + (pats[0]),0,255,frame[:,:,2])
    #frame = cv2.cvtColor(frame.astype(np.uint8),cv2.COLOR_HSV2RGB)

    cv2.imshow('o',frame)
    #cv2.imwrite('out.png',frame[:284,:253])

    bri = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)[:,:,2]
    r,t = detch(bri)
    detpat(bri,r,t)

    '''
    invc = cv2.VideoCapture('/home/user/fin/MVI_9100.MOV')
    _,sframe = invc.read()
    _,sframe = invc.read()
    _,sframe = invc.read()
    _,sframe = invc.read()
    _,sframe = invc.read()

    off = 10
    frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV)[:,:,2][off:off + 512,off:off + 512]
    cv2.imshow('s',frame)
    detpat(frame)
    '''

    cv2.waitKey(0)
    cv2.destroyAllWindows()

