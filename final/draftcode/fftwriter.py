invc = cv2.VideoCapture('/home/user/Downloads/test.mkv')
fourcc = cv2.VideoWriter_fourcc(*'X264')
outvc = cv2.VideoWriter('/x/test.avi',fourcc,60,(scale,scale))
#invc = cv2.VideoCapture('/home/user/fin/MVI_9099.MOV')

inv = 1
index = 0
for i in range(800):
    _,sframe = invc.read()
    sframe = sframe[:scale,:scale]

    '''
    frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV).astype(np.float32)
    cv2.imshow('x',frame[:,:,2].astype(np.uint8))
    detpat(frame[:,:,2])
    cv2.waitKey(0)

    continue
    '''

    for j in range(2):
        print(index)
        index += 1

        frame = cv2.cvtColor(sframe,cv2.COLOR_RGB2HSV).astype(np.float32)
        np.clip(frame[:,:,2] * 0.8 + 25.6 + (pats[1] * inv),0,255,frame[:,:,2])
        frame = cv2.cvtColor(frame.astype(np.uint8),cv2.COLOR_HSV2RGB)
        outvc.write(frame)
        inv *= -1
