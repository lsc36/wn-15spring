import cv2
import numpy as np
import time

invc = cv2.VideoCapture('Downloads/out.mkv')
fourcc = cv2.VideoWriter_fourcc(*'X264')
out = cv2.VideoWriter('out.avi',fourcc,60,(1920,1080))

chess_b = np.full((64,64,3),[1,1,0.5])
chess_w = np.full((64,64,3),[1,1,1])
chess = np.concatenate(
        [np.concatenate([chess_b,chess_w] * 9),np.concatenate([chess_w,chess_b] * 9)] * 15,
        axis = 1)
chess_inv = np.concatenate(
        [np.concatenate([chess_w,chess_b] * 9),np.concatenate([chess_b,chess_w] * 9)] * 15,
        axis = 1)

chess = chess[0:1080,0:1920]
chess_inv = chess_inv[0:1080,0:1920]

seq = [1,0] * 1000000
index = 0
sframe = None
while True:
    print(index)

    if index % 2 == 0:
        if not invc.isOpened():
            break
        _,sframe = invc.read()

    frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV_FULL)
    if seq[index] == 1:
        frame = frame * chess
    else:
        frame = frame * chess_inv

    frame = frame.astype(np.uint8)
    oframe = cv2.cvtColor(frame,cv2.COLOR_HSV2RGB_FULL)
    out.write(oframe)

    index += 1

out.release()
cv2.destroyAllWindows()
