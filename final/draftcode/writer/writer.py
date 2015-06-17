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

def gen_locate():
    locate = np.full((LOCATE_SIZE,LOCATE_SIZE),255,dtype = np.uint8)
    elm = LOCATE_SIZE / 7
    locate[elm * 1:elm * 6,elm * 1:elm * 6] = 0
    locate[elm * 2:elm * 5,elm * 2:elm * 5] = 255

    i_locate = cv2.cvtColor(locate,cv2.COLOR_GRAY2RGB)

    return i_locate

i_frame = cv2.cvtColor(np.full((H,W),0,dtype = np.uint8),cv2.COLOR_GRAY2RGB)

i_locate = gen_locate()
i_frame[PAD_H + 0:PAD_H + LOCATE_SIZE,PAD_W + 0:PAD_W + LOCATE_SIZE] = i_locate
i_frame[PAD_H + 0:PAD_H + LOCATE_SIZE,W - LOCATE_SIZE - PAD_W:W - PAD_W] = i_locate
i_frame[H - LOCATE_SIZE - PAD_H:H - PAD_H,PAD_W + 0:PAD_W + LOCATE_SIZE] = i_locate
i_frame[H - LOCATE_SIZE - PAD_H:H - PAD_H,W - LOCATE_SIZE - PAD_W:W - PAD_W] = i_locate

invc = cv2.VideoCapture('out.mkv')
fourcc = cv2.VideoWriter_fourcc(*'X264')
out = cv2.VideoWriter('test.avi',fourcc,T_FPS,(1920,1080))


chess_b = np.full((64,64,3),[1,1,0.5])
chess_w = np.full((64,64,3),[1,1,1])
chess = np.concatenate(
        [np.concatenate([chess_b,chess_w] * 9),np.concatenate([chess_w,chess_b] * 9)] * 15,
        axis = 1)
chess_inv = np.concatenate(
        [np.concatenate([chess_w,chess_b] * 9),np.concatenate([chess_b,chess_w] * 9)] * 15,
        axis = 1)

chess = chess[0:CH,0:CW]
chess_inv = chess_inv[0:CH,0:CW]

seq = [1,0] * 1000000


index = 0
while index < 10000:
    _,sframe = invc.read()
    if sframe == None:
        break
    frame = cv2.resize(sframe,(CW,CH))
    for repeat in range(T_FPS // O_FPS):
        print(index)
        
        frame = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV_FULL)
        if seq[index] == 1:
            frame = frame * chess
        else:
            frame = frame * chess_inv

        frame = cv2.cvtColor(frame.astype(np.uint8),cv2.COLOR_HSV2RGB_FULL)

        i_frame[CPAD_H:H - CPAD_H,CPAD_W:W - CPAD_W] = frame
        out.write(i_frame)
        index += 1

out.release()
