#!/usr/bin/env python

import os
import cv2
import numpy as np
import re
from multiprocessing import Pool
from multiprocessing import Process

last_mark = 0
filter_ths = 10

def getLine(ci):
    #elem = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
    #ci = cv2.erode(cv2.dilate(ci,elem),elem)
    h,w = ci.shape
    ci = cv2.Canny(ci,120,180)
    gapline = cv2.HoughLinesP(ci,1,np.pi / 180,w / 32)[0]
    yl = list();
    for line in gapline:
        yl.append((line[1] + line[3]) / 2)
    return yl

def mergeLine(yl):
    ret = list()
    yl.sort()
    maxgap = 0
    for i in range(len(yl) - 1):
        maxgap = max(maxgap,yl[i + 1] - yl[i])
    for i in range(len(yl) - 1):
        if yl[i + 1] - yl[i] > maxgap / 8:
            ret.append(yl[i])
    ret.append(yl[-1])
    return ret

def fixGap(gl):
    wl = list()
    last = gl[0]
    for y in gl[1:]:
        wl.append(y - last)
        last = y
    wl.sort()
    s = wl[0]
    f = [wl[0]]
    for c,w in enumerate(wl[1:]):
        if w < (s / len(f)) * 2:
            s += w
            f.append(w)
    avg = s / len(f)

    ret = [gl[0]]
    last = gl[0]
    for y in gl[1:]:
        gap = y - last
        if gap * 3 >= avg * 2:
            t = int(round(float(gap) / float(avg)))
            for i in range(t - 1):
                ret.append(last + gap * (i + 1) / t)
        ret.append(y)
        last = y

    return ret

def getBit(ci,gline,se,ee):
    global filter_ths

    h,w = ci.shape
    si = ci.sum(axis = 1)

    gs = gline[se]
    ge = gline[ee]
    mid = (gs + ge) / 2
    gap = ge - gs
    s = mid - gap / 3
    e = mid + gap / 3

    '''
    avga = 0
    avgb = 0
    c = 0
    for i in range(max(0,gs - gap),gs):
        avga += si[i]
        c += 1
    if c > 0:
        avga = avga / c * 3 / 4
    c = 0
    for i in range(ge,min(h,ge + gap)):
        avgb += si[i]
        c += 1
    if c > 0:
        avgb = avgb / c * 3 / 4
    '''

    avg = si[gs:ge].sum() // gap

    ths = max(filter_ths * w,avg * 2 // 3)
    c = 0
    for i in range(s + 1,e):
        if si[i] >= ths:
            c += 1
    if c * 3 > (e - s) * 2:
        #print(float(c) / float((e - s)))
        return True
    return False

def getMap(gline, gi):
    global last_mark

    gstr = ''
    for i in range(len(gline) - 1):
        if getBit(gi,gline,i,i + 1):
            gstr += '1'
        else:
            gstr += '0'
    print(gstr)

    ba = None
    bb = None
    gp = re.search('0101010111010111',gstr)
    if gp != None:
        ba = gp.start()
    gp = re.search('0101010101010111',gstr) 
    if gp != None:
        bb = gp.start()

    if ba == None and bb == None:
        return None

    if ba == None:
        bass = bb
    elif bb == None:
        bass = ba
    else:
        bass = min(ba,bb)
    #elif last_mark == 1:
    #    bass = ba
    #elif last_mark == 2:
    #    bass = bb

    print(bass)
    msgmap = list(range(bass,bass + 16))
    return msgmap

    '''
    msgmap = []
    i = base
    c = 0
    while i < (base + len(''.join(re.findall(pat,gstr[base:])))):
        msgmap.append(i)
        if gstr[i] == '1':
            c += 1
            if (c == 3 and lt == False):
                break
        else:
            c = 0
        i += 1
    i = base - 1
    bmsgmap = []
    while (len(msgmap) + len(bmsgmap)) < 16:
        bmsgmap.append(i)
        i -= 1   
    bmsgmap.reverse()
    msgmap += bmsgmap
    return msgmap
    '''

def decode(ci,gline,msgmap):
    msg = ''
    for i in msgmap:
        if getBit(ci,gline,i,i + 1):
            msg += '1'
        else:
            msg += '0'
    return msg

def preprocess(path):
    img = cv2.imread(path,cv2.CV_LOAD_IMAGE_COLOR)
    img = cv2.flip(img,0)
    imgH,imgW,_ = img.shape
    bi,gi,ri = cv2.split(img)

    _,gi = cv2.threshold(gi,filter_ths,128,cv2.THRESH_TOZERO)
    _,ri = cv2.threshold(ri,filter_ths,128,cv2.THRESH_TOZERO)
    _,bi = cv2.threshold(bi,filter_ths,128,cv2.THRESH_TOZERO)

    gline = getLine(gi[0:imgH,imgW / 2:imgW])
    gline = fixGap(mergeLine(gline))
    msgmap = getMap(gline, gi)
    if msgmap == None:
        gline = getLine(gi[0:imgH,0:imgW / 2])
        gline = fixGap(mergeLine(gline))
        msgmap = getMap(gline, gi)
    assert msgmap != None

    mark = int(decode(gi,gline,msgmap),2)
    assert mark == 0x5557 or mark == 0x55D7
    
    msga = decode(ri,gline,msgmap)
    msgb = decode(bi,gline,msgmap)

    return (mark,msga,msgb)

def run():
    global last_mark, filter_ths

    pool = Pool(processes = 12)
    idx = 1
    images = []
    while True:
        path = 'out%03d.bmp'%idx
        if not os.access(path,os.R_OK):
            break
        images.append(path)
        idx += 1

    result = pool.map(preprocess,images)
    
    ans = ''
    for mark,msga,msgb in result:
        if mark == 0x5557:
            mark = 1
        else:
            mark = 2

        if mark == last_mark:
            print('repeat')
            continue
        last_mark = mark

        msga = int(msga,2) ^ 0xD573
        msgb = int(msgb,2) ^ 0xD573

        out = [0,0,0,0]
        out[0] = msga & 0xFF
        out[1] = (msga & 0xFF00) >> 8
        out[2] = msgb & 0xFF
        out[3] = (msgb & 0xFF00) >> 8
        
        for c in out:
            print(hex(c))
            if c > 0:
                print(chr(c))
                ans += chr(c)

    print(ans)
    return ans

    '''
    idx = 1
    ans = ''
    while True:
        print(idx)
        idx += 1

        try:
            img = cv2.imread('data/5/out%03d.bmp'%idx,cv2.CV_LOAD_IMAGE_COLOR)
            if img == None:
                break
            img = cv2.flip(img,0)
            imgH,imgW,_ = img.shape
            bi,gi,ri = cv2.split(img)

            _,gi = cv2.threshold(gi,filter_ths,128,cv2.THRESH_TOZERO)
            _,ri = cv2.threshold(ri,filter_ths,128,cv2.THRESH_TOZERO)
            _,bi = cv2.threshold(bi,filter_ths,128,cv2.THRESH_TOZERO)

            gline = getLine(gi[0:imgH,imgW / 2:imgW])
            gline = fixGap(mergeLine(gline))
            msgmap = getMap(gline, gi)
            if msgmap == None:
                gline = getLine(gi[0:imgH,0:imgW / 2])
                gline = fixGap(mergeLine(gline))
                msgmap = getMap(gline, gi)
            assert msgmap != None

            mark = int(decode(gi,gline,msgmap),2)
            assert mark == 0x5557 or mark == 0x55D7
            #assert False

            if mark == 0x5557:
                mark = 1
            else:
                mark = 2

            if mark == last_mark:
                print('repeat')
                continue
            last_mark = mark

            msga = decode(ri,gline,msgmap)
            msgb = decode(bi,gline,msgmap)

            out = [0,0,0,0]
            out[0] = int(msga,2) & 0xFF
            out[1] = (int(msga,2) & 0xFF00) >> 8
            out[2] = int(msgb,2) & 0xFF
            out[3] = (int(msgb,2) & 0xFF00) >> 8
            
            for c in out:
                print(hex(c))
                if c > 0:
                    print(chr(c))
                    ans += chr(c)

        except Exception as e:
            print(e)
            for y in gline:
                cv2.line(ri,(0,y),(imgW,y),255,1)
                cv2.line(gi,(0,y),(imgW,y),255,1)
                cv2.line(bi,(0,y),(imgW,y),255,1)
            cv2.imshow('img',img)
            cv2.imshow('R',ri)
            cv2.imshow('G',gi)
            cv2.imshow('B',bi)
            if (cv2.waitKey(0) & 0xFF) == 27:
                cv2.destroyAllWindows()
                break
            cv2.destroyAllWindows()

    print(ans)
    return ans
    '''

if __name__ == '__main__':
    run()
