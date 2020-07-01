import time
import threading
import cv2
import numpy as np


class KapinaCam:
    """
    Abstraction for attached camera equipment.
    Due to silly buffering of webcam hardware and openCV the camera is constantly running in the background.
    Snapshots are only saved when instructed to do so.

    A minimum interval can be set to avoid saving snapshots too rapidly.
    """
    def __init__(self,
                 write_sem,
                 output_file,
                 camera_id=0,
                 capture_interval=0.5,
                 min_save_interval=1,
                 y_crop=(233, 520),
                 x_crop=(632, 1042),
                 zoom_factor=2,
                 sharpen=True):
        """
        Holy shit this is a lot of parameters
        :param write_sem:
        :param output_file:
        :param camera_id:
        :param capture_interval:
        :param min_save_interval:
        :param y_crop:
        :param x_crop:
        :param zoom_factor:
        :param sharpen:
        """

        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.capture_interval = capture_interval

        self.output_file = output_file
        self.min_save_interval = min_save_interval
        self.y_crop = y_crop
        self.x_crop = x_crop
        self.zoom_factor = zoom_factor
        self.sharpen = sharpen

        self.write_sem: threading.Semaphore = write_sem
        self.elapsed = min_save_interval
        self.start = 0

        self.camera_sem = threading.Semaphore(1)
        self.frame = None

        self.unsharp_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

        threading.Thread(target=self.videocapture).start()

    def videocapture(self):
        """
        Continuously reads camera output and updates the buffer frame of this instance
        :return: None
        """
        while True:
            with self.camera_sem:
                ret, self.frame = self.cap.read()
            time.sleep(self.capture_interval)

    def snapshot(self):
        """
        Saves the current buffer frame to file if given minimum interval has elapsed from last save
        :return: None
        """
        self.elapsed = time.time() - self.start
        if self.elapsed < self.min_save_interval:
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
