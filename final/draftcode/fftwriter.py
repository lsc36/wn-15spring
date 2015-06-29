import numpy as np
import cv2
import fftutils

invc = cv2.VideoCapture('/home/user/Downloads/out.mkv')
fourcc = cv2.VideoWriter_fourcc(*'I420')
outvc = cv2.VideoWriter('/x/test.avi',fourcc,60,(fftutils.W,fftutils.H))

syms = fftutils.gensymbol(23,fftutils.SYMLEN,fftutils.SYMNUM)
pats = fftutils.genpat(syms)
#for pat in pats:
#    cv2.imshow('dframe',pat.astype(np.uint8) + 128)
#    cv2.waitKey(0)

inv = 1
index = 0

def gendata(index,x):
    assert(x < 64)
    return (x << 2) | (index % 4)

data = [0,1,2,4096,4,5,2091,7,8,9,30,31,32,43,54,61] * 1000
for i in range(800):
    _,sframe = invc.read()
    sframe = cv2.resize(sframe,(fftutils.W,fftutils.H))
    d = gendata(index,data[index])

    for j in range(2):
        pat = fftutils.extendpat(pats[d],(fftutils.W,fftutils.H))

        frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV).astype(np.float)
        np.clip(frame[:,:,2] * 0.8 + 25.6 + (pat * inv),0,255,frame[:,:,2])
        frame = cv2.cvtColor(frame.astype(np.uint8),cv2.COLOR_HSV2RGB)
        outvc.write(frame)

        inv *= -1

    print(index)
    index += 1

invc.release()
outvc.release()
