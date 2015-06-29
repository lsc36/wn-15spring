import numpy as np
import cv2
import math
import utils
import json
from collections import defaultdict

H = 1080
W = 1920
SYMLEN = 30
SYMNUM = 128

def gensymbol(seed,size,num):
    '''
    np.random.seed(seed)
    vecs = []
    for idx in range(num):
        while True:
            vec = list(map(lambda x: np.random.uniform(0.0,400000),range(size)))
            flag = False
            for v in vecs:
                if np.corrcoef(vec,v)[0,1] > 0.3:
                    flag = True
                    break
            if not flag:
                break
        print(idx)
        vecs.append(vec)
    '''
    return json.load(open('128sym.json','r'))

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

def genpat(syms):
    scale = 512
    radius = (scale / 2) * 0.162
    #sympos = genpos(radius,scale)
    sympos = genpos(radius * 1.5,scale)
    sympos += genpos(radius * 2,scale)
    #sympos += genpos(radius * 2.5,scale)
    #sympos += genpos(radius * 3,scale)

    def _ru(deep):
        if deep <= 0:
            return [[]]
        vecs = []
        for sym in syms:
            vec = list(map(lambda x:
                x * np.exp(1j * np.random.uniform(0,np.pi * 2)),sym))
            vec.extend(np.conj(vec))
            vecs.extend(list(map(lambda x:
                vec + x,_ru(deep - 1))))
        return vecs

    vecs = _ru(2)
    pats = []
    index = 0
    for vec in vecs:
        print(index)
        index += 1

        spt = np.zeros((scale,scale),dtype = np.complex)
        for idx,v in enumerate(vec):
            spt[sympos[idx]] = v
        pat = np.round(np.real(np.fft.ifft2(np.fft.ifftshift(spt))))

        print(np.max(np.abs(pat)))
        assert(np.max(np.abs(pat)) > 20 and np.max(np.abs(pat)) < 100)
        
        pats.append(pat)

    #cv2.imshow('x',spt.astype(np.uint8) + 128)
    #tmp = np.abs(np.fft.fftshift(np.fft.fft2(pat + 128)))
    #cv2.imshow('y',(np.log10(np.maximum(1,tmp)) * 20).astype(np.uint8))
    #cv2.waitKey(0)

    return pats

def extendpat(pat,size):
    hr,wr = pat.shape
    wr = (size[0] - 1) // wr + 1
    hr = (size[1] - 1) // hr + 1
    return cv2.repeat(pat,hr,wr)[:size[1],:size[0]]

def corch(sym,spt,rrange,trange):
    scale,_ = spt.shape
    maxc = -1
    maxr = (0,0)
    log = defaultdict(list)
    rrange = np.clip(rrange,30,200)
    for r in range(rrange[0],rrange[1]):
        for theta in range(trange[0],trange[1]):
            sympos = genpos(r,scale,theta * np.pi / 180)
            vec = list(map(lambda x: spt[x],sympos))
            cor = np.corrcoef(sym * 2,vec)[0,1]
            log[theta].append((cor,r,theta))
            if cor > maxc:
                maxc = cor
                maxr = (r,theta)
    return sorted(log[maxr[1]],key = lambda x: x[0],reverse = True)

def detch(sym,pat):
    spt = np.abs(np.fft.fftshift(np.fft.fft2(pat.astype(np.float))))
    spt = cv2.GaussianBlur(spt,(3,3),0)

    tents = corch(sym,spt,(30,150),(-45,45))
    ents = [tents[0],None]
    for cor,r,t in tents:
        if abs(r - ents[0][1]) > 10:
            ents[1] = (cor,r,t)
            break

    print(ents[0])
    print(ents[1])

    tmp = np.clip(spt / 1000,0,255).astype(np.uint8)
    cv2.circle(tmp,(spt.shape[1] // 2,spt.shape[0] // 2),ents[0][1],(255,0,0))
    cv2.imshow('ch',tmp)

    if min(ents[0][0],ents[1][0]) < 0.7:
        return None

    ents = sorted(ents,key = lambda x: x[1])
    return (ents[0][1:],ents[1][1:])

def optch(hints):
    nchs = []
    for pat,sym,ch in hints:
        spt = np.abs(np.fft.fftshift(np.fft.fft2(pat.astype(np.float))))
        spt = cv2.GaussianBlur(spt,(3,3),0)

        r,t = ch
        ch = corch(sym,spt,(r - 2,r + 2),(t - 1,t + 1))[0]
        if ch[0] < 0.7:
            nchs.append((r,t))
        else:
            nchs.append(ch[1:])

    tmp = np.clip(spt / 1000,0,255).astype(np.uint8)
    cv2.circle(tmp,(spt.shape[1] // 2,spt.shape[0] // 2),nchs[0][0],(255,0,0))
    cv2.circle(tmp,(spt.shape[1] // 2,spt.shape[0] // 2),nchs[1][0],(255,0,0))
    cv2.imshow('ch',tmp)

    return nchs

def detpat(syms,pat,ch):
    radius,theta = ch
    paty,patx = pat.shape
    scale = patx

    spt = np.abs(np.fft.fftshift(np.fft.fft2(pat.astype(np.float))))
    spt = cv2.GaussianBlur(spt,(3,3),0)
    sympos = genpos(radius,scale,theta * np.pi / 180)

    vec = list(map(lambda x: spt[x],sympos))
    maxc = -1
    maxidx = 0
    for idx,sym in enumerate(syms):
        cor = np.corrcoef(sym * 2,vec)[0,1]
        if cor > 0.1:
            print(cor)
        if cor > maxc:
            maxidx = idx
            maxc = cor

    return maxidx,maxc

