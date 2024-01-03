from random import randint
import cv2
import Person
import time
import pyttsx3
import requests
import sys
import ibmiotf.application
import ibmiotf.device
import numpy as np

organization = "6yocvj"
deviceType = "PeopleCounter"
deviceId = "12345"
authMethod = "token"
authToken = "12345678"

engine = pyttsx3.init()
engine.say('Hello')
engine.runAndWait()

# Counters for entry and exit
cnt_up = 0
cnt_down = 0

# Video source
# cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture('people.mp4')

# Video properties
cap = cv2.VideoCapture('people.mp4')
# cap = cv2.VideoCapture(0)

for i in range(19):
    print(i, cap.get(i))

w = cap.get(3)
h = cap.get(4)
frameArea = h * w
areaTH = frameArea / 250
print('Area Threshold', areaTH)

# Entry/exit lines
line_up = int(2 * (h / 5))
line_down = int(3 * (h / 5))
up_limit = int(1 * (h / 5))
down_limit = int(4 * (h / 5))

print("Red line y:", str(line_down))
print("Blue line y:", str(line_up))

line_down_color = (255, 0, 0)
line_up_color = (0, 0, 255)

pt1 = [0, line_down]
pt2 = [w, line_down]
pts_L1 = np.array([pt1, pt2], np.int32)
pts_L1 = pts_L1.reshape((-1, 1, 2))

pt3 = [0, line_up]
pt4 = [w, line_up]
pts_L2 = np.array([pt3, pt4], np.int32)
pts_L2 = pts_L2.reshape((-1, 1, 2))

pt5 = [0, up_limit]
pt6 = [w, up_limit]
pts_L3 = np.array([pt5, pt6], np.int32)
pts_L3 = pts_L3.reshape((-1, 1, 2))

pt7 = [0, down_limit]
pt8 = [w, down_limit]
pts_L4 = np.array([pt7, pt8], np.int32)
pts_L4 = pts_L4.reshape((-1, 1, 2))

# Background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

# Structural elements for morphological filters
kernelOp = np.ones((3, 3), np.uint8)
kernelOp2 = np.ones((5, 5), np.uint8)
kernelCl = np.ones((11, 11), np.uint8)

# Variables
font = cv2.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1


def ibmwork(cnt_up, cnt_down, deviceCli):
    data = {'UP': cnt_up, 'down': cnt_down}

    def myOnPublishCallback():
        print("Published Up People Count = %s" % str(cnt_up),
              "Down People Count = %s " % str(cnt_down), "to IBM Watson")

    success = deviceCli.publishEvent("PeopleCounter", "json", data, qos=0, on_publish=myOnPublishCallback)
    if not success:
        print("Not connected to IoTF")


def ibmstart(cnt_up, cnt_down):
    try:
        deviceOptions = {
            "org": organization,
            "type": deviceType,
            "id": deviceId,
            "auth-method": authMethod,
            "auth-token": authToken
        }
        deviceCli = ibmiotf.device.Client(deviceOptions)
        print(type(deviceCli))
    except Exception as e:
        print("Caught exception connecting device: %s" % str(e))
        sys.exit()

    deviceCli.connect()
    ibmwork(cnt_up, cnt_down, deviceCli)


while cap.isOpened():
    ret, frame = cap.read()

    for i in persons:
        i.age_one()  # age every person one frame

    # PRE-PROCESSING #
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    try:
        ret, imBin = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
        ret, imBin2 = cv2.threshold(fgmask2, 200, 255, cv2.THRESH_BINARY)

        mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
        mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
    except:
        print('EOF')
        print('UP:', cnt_up)
        print('DOWN:', cnt_down)
        break

    # CONTOURS #
    contours0, hierarchy = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours0:
        area = cv2.contourArea(cnt)
        if area > areaTH:
            M = cv2.moments(cnt)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            x, y, w, h = cv2.boundingRect(cnt)
            new = True

            if cy in range(up_limit, down_limit):
                for i in persons:
                    if abs(cx - i.getX()) <= w and abs(cy - i.getY()) <= h:
                        new = False
                        i.updateCoords(cx, cy)

                if i.going_UP(line_down, line_up) == True:
                    cnt_up += 1
                    print("ID:", i.getId(), 'crossed going up at', time.strftime("%c"))
                    engine.say('A Person is Going UP ')
                    engine.runAndWait()
                elif i.going_DOWN(line_down, line_up) == True:
                    cnt_down += 1
                    print("ID:", i.getId(), 'crossed going down at', time.strftime("%c"))
                    engine.say('A Person is Going Down')
                    engine.runAndWait()
                    break

                if i.getState() == '1':
                    if i.getDir() ==
