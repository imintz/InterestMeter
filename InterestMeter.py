import picamera
from picamera.array import PiRGBArray
import time
import cv2
import RPi.GPIO as GPIO
import argparse

# Set up argument parsing
parser = argparse.ArgumentParser(description='Computer vision based interest meter')
parser.add_argument('-g', action='store_true')
args = parser.parse_args()

FRAME_THRESHOLD = 5
TIME_THRESHOLD = 5 # In seconds

def SetupGPIO():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, False)

def SetupCamera():
    camera = picamera.PiCamera()
    camera.vflip = True
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))
    time.sleep(0.1)
    return (camera, rawCapture)

def SetupCascadeClassifier():
    face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    assert face_cascade.empty() == False
    return face_cascade

def LedOn():
    GPIO.output(7, True)

def LedOff():
    GPIO.output(7, False)

class InterestMeter:
    def __init__(self):
        self.timer = 0
        self.startCounter = 0
        self.stopCounter = 0
    def AssessInterest(self, faceFound):
        if not faceFound:
            if self.timer == 0:
                self.startCounter = 0
            else:
                self.stopCounter+=1
                if self.stopCounter > FRAME_THRESHOLD:
                    self.timer = 0
                    LedOff()
        else:
            if self.timer == 0:
                self.startCounter+=1
                if self.startCounter > FRAME_THRESHOLD:
                   self.timer = time.time() 
            else:
                self.stopCounter = 0
                if time.time() - self.timer > TIME_THRESHOLD:
                    LedOn()

def Cleanup():
    cv2.destroyAllWindows()
    GPIO.cleanup()

# Actual Program Begins
camera, rawCapture = SetupCamera()
SetupGPIO()
face_cascade = SetupCascadeClassifier()
meter = InterestMeter()

try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        meter.AssessInterest(len(faces))

        # Display image in Gui if flag is set
        if args.g:
            for x, y, w, h in faces:
                cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.imshow("Frame", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        rawCapture.truncate(0)
except KeyboardInterrupt:
    pass
Cleanup()
