import cv2
import numpy as np
import time
import random
from utils import *

def gen_locate():
    locate = np.full((LOCATE_SIZE,LOCATE_SIZE),255,dtype = np.uint8)
    elm = LOCATE_SIZE / 7
    locate[elm * 1:elm * 6,elm * 1:elm * 6] = 0
    locate[elm * 2:elm * 5,elm * 2:elm * 5] = 255
    i_locate = cv2.cvtColor(locate,cv2.COLOR_GRAY2RGB)
    return i_locate

def gen_halign():
    block = np.full((16,16),255,dtype = np.uint8)
    bar = np.full((16,CW,3),255,dtype = np.uint8)
    return bar
    '''
    for i in range(0,CW,32):
        bar[:,i:i + 16,2] = block
    return cv2.cvtColor(bar,cv2.COLOR_HSV2RGB_FULL)
    '''

def gen_valign():
    block = np.full((16,16),255,dtype = np.uint8)
    bar = np.full((CH,16,3),255,dtype = np.uint8)
    return bar
    '''
    for i in range(0,CH,32):
        bar[i:i + 16,:,2] = block
    return cv2.cvtColor(bar,cv2.COLOR_HSV2RGB_FULL)
    '''

i_frame = cv2.cvtColor(np.full((H,W),0,dtype = np.uint8),cv2.COLOR_GRAY2RGB)
i_locate = gen_locate()
i_frame[PAD_H + 0:PAD_H + LOCATE_SIZE,PAD_W + 0:PAD_W + LOCATE_SIZE] = i_locate
i_frame[PAD_H + 0:PAD_H + LOCATE_SIZE,W - LOCATE_SIZE - PAD_W:W - PAD_W] = i_locate
i_frame[H - LOCATE_SIZE - PAD_H:H - PAD_H,PAD_W + 0:PAD_W + LOCATE_SIZE] = i_locate
i_frame[H - LOCATE_SIZE - PAD_H:H - PAD_H,W - LOCATE_SIZE - PAD_W:W - PAD_W] = i_locate

bar = gen_halign()
bh,bw,_ = bar.shape
i_frame[PAD_H + (LOCATE_SIZE - bh) // 2:PAD_H + (LOCATE_SIZE + bh) // 2,CPAD_W:W - CPAD_W] = bar
i_frame[H - PAD_H - (LOCATE_SIZE + bh) // 2:H - PAD_H - (LOCATE_SIZE - bh) // 2,CPAD_W:W - CPAD_W] = bar
bar = gen_valign()
bh,bw,_ = bar.shape
i_frame[CPAD_H:H - CPAD_H,PAD_W + (LOCATE_SIZE - bw) // 2:PAD_W + (LOCATE_SIZE + bw) // 2] = bar
i_frame[CPAD_H:H - CPAD_H,W - PAD_W - (LOCATE_SIZE + bw) // 2:W - PAD_W - (LOCATE_SIZE - bw) // 2] = bar

invc = cv2.VideoCapture('/home/user/Downloads/test2.mkv')
#fourcc = cv2.VideoWriter_fourcc(*'I420')
fourcc = cv2.VideoWriter_fourcc(*'X264')
out = cv2.VideoWriter('/x/test.avi',fourcc,T_FPS,(1920,1080))


msg = 'HardcoreTano*C'
data = modul(msg,78)
kframes = genkframe(23)
dframe = np.zeros((CH,CW))
index = 0
for y in range(0,CH,B):
    for x in range(0,CW,B):
        dframe[y:y + B,x:x + B] = kframes[data[index]]
        index += 1

#cv2.imshow('d',(dframe + 128).astype('uint8'))
#cv2.waitKey(0)


seq = ([-1,1] * 30) * 100000
index = 0
while index < 4000000:
    _,sframe = invc.read()
    if sframe is None:
        break
    #sframe = sframe[CPAD_H:CPAD_H + CH,CPAD_W:CPAD_W + CW]
    sframe = cv2.resize(sframe,(CW,CH))
    for repeat in range(T_FPS // O_FPS):
        print(index)
        frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV).astype(np.int)

        #ch = chess_r[seq[index]]
        ch = dframe * seq[index]
        bri = frame[:,:,2]
        sta = frame[:,:,1]
        bri = np.clip(bri * 0.8 + 25.6 + ch,0,255)
        #sta2 = np.clip(sta + bri * 0.05 * ch,0,255)
        frame[:,:,2] = bri
        frame = cv2.cvtColor(frame.astype(np.uint8),cv2.COLOR_HSV2RGB)

        i_frame[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W] = frame
        #cv2.imshow('x2',i_frame)
        #cv2.waitKey(0)
        out.write(i_frame)
        index += 1

out.release()
cv2.destroyAllWindows()
