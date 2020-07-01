import time
import threading
import cv2
import numpy as np


class KapinaCam:
    def __init__(self,
                 write_sem,
                 output_file,
                 camera_id=0,
                 min_interval=1,
                 y_crop=(233, 520),
                 x_crop=(632, 1042),
                 zoom_factor=2,
                 sharpen=True):

        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.output_file = output_file
        self.min_interval = min_interval
        self.y_crop = y_crop
        self.x_crop = x_crop
        self.zoom_factor = zoom_factor
        self.sharpen = sharpen

        self.write_sem: threading.Semaphore = write_sem
        self.elapsed = min_interval
        self.start = 0

        self.camera_sem = threading.Semaphore(1)
        self.frame = None

        self.unsharp_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

        threading.Thread(target=self.videocapture).start()

    def videocapture(self):
        while True:
            with self.camera_sem:
                ret, self.frame = self.cap.read()
            time.sleep(0.5)

    def snapshot(self):
        self.elapsed = time.time() - self.start
        if self.elapsed < self.min_interval:
            return

        self.start = time.time()

        with self.camera_sem:
            frame = self.frame
        # Cropping
        frame = frame[self.y_crop[0]:self.y_crop[1], self.x_crop[0]:self.x_crop[1]]

        # Resizing
        w = int(frame.shape[1] * self.zoom_factor)
        h = int(frame.shape[0] * self.zoom_factor)
        dim = (w, h)
        frame = cv2.resize(frame, dim)

        # Sharpening (Using convolution magic and unsharp mask (USM) technique)
        if self.sharpen:
            frame = cv2.filter2D(frame, -1, self.unsharp_kernel)

        with self.write_sem:
            print("Saved picture")
            cv2.imwrite(self.output_file, frame)
