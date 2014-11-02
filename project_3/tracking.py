"""Project 3: Tracking.

In this project, you'll track objects in videos.
"""

import cv2
import math
import numpy as np


def track_ball_1(video):
    """Track the ball's center in 'video'.

    Arguments:
      video: an open cv2.VideoCapture object containing a video of a ball
        to be tracked.

    Outputs:
      a list of (min_x, min_y, max_x, max_y) four-tuples containing the pixel
      coordinates of the rectangular bounding box of the ball in each frame.
    """

    out_list = []

    radius_avg = 0
    radius_num = 0
    radius_final = 0

    while (True):
        ret, frame = video.read()
        frame = cv2.medianBlur(frame, 1)
        if (ret == False):
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(frame, cv2.cv.CV_HOUGH_GRADIENT, 2, 1000,
                                    param1=20, param2=20, minRadius=30, maxRadius=40)
        circles = np.uint16(np.around(circles))

        radius_avg += circles[0][0][2]
        radius_num += 1
        radius_final = radius_avg / radius_num
        out_list.append((circles[0][0][0] - radius_final, circles[0][0][1] - radius_final, circles[0][0][0] + radius_final, circles[0][0][1] + radius_final)) 

    print out_list
    return out_list

def track_ball_2(video):
    """As track_ball_1, but for ball_2.mov."""
    pass


def track_ball_3(video):
    """As track_ball_1, but for ball_2.mov."""
    pass


def track_ball_4(video):
    """As track_ball_1, but for ball_2.mov."""
    pass


def track_face(video):
    """As track_ball_1, but for face.mov."""
    pass
