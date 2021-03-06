#!/usr/bin/env python
"""Project 2: Stereo vision.

In this project, you'll extract dense 3D information from stereo image pairs.
"""

import cv2
import math
import numpy as np
from matplotlib import pyplot as plt
import StringIO


def rectify_pair(image_left, image_right, viz=False):
    """Computes the pair's fundamental matrix and rectifying homographies.

    Arguments:
      image_left, image_right: 3-channel images making up a stereo pair.

    Returns:
      F: the fundamental matrix relating epipolar geometry between the pair.
      H_left, H_right: homographies that warp the left and right image so
        their epipolar lines are corresponding rows.
    """
    sift = cv2.SIFT()
    height, width, depth = image_left.shape
    # find features and descriptors
    kp1, des1 = sift.detectAndCompute(image_left, None)
    kp2, des2 = sift.detectAndCompute(image_right, None)

    # FLANN parameters
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    pts1 = []
    pts2 = []
    # ratio scientifically chosen to be best
    for i, (m, n) in enumerate(matches):
        if m.distance < 0.65*n.distance:
            pts2.append(kp2[m.trainIdx].pt)
            pts1.append(kp1[m.queryIdx].pt)
    pts1 = np.float32(pts1)
    pts2 = np.float32(pts2)
    fMat, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 3, 0.99)
    # cv2.FM_LMEDS) # this appears to work the same
    h1 = np.empty((3, 3))
    h2 = np.empty((3, 3))
    cv2.stereoRectifyUncalibrated(
        pts1.flatten(), pts2.flatten(), fMat,
        (height, width), h1, h2, threshold=3)
    return fMat, h1, h2


def disparity_map(image_left, image_right):
    """Compute the disparity images for image_left and image_right.

    Arguments:
      image_left, image_right: rectified stereo image pair.

    Returns:
      an single-channel image containing disparities in pixels,
        with respect to image_left's input pixels.
    """
    window_size = 3
    min_disp = 16
    num_disp = 112-min_disp
    stereo = cv2.StereoSGBM(
        minDisparity=min_disp,
        numDisparities=num_disp,
        SADWindowSize=window_size,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32,
        disp12MaxDiff=1,
        P1=8*3*window_size**2,
        P2=32*3*window_size**2,
        fullDP=False
        )

    disp_1 = stereo.compute(image_left, image_right) / 16
    disp_1 = np.array(disp_1, dtype='uint8')

    return disp_1


def point_cloud(disparity_image, image_left, focal_length):
    """Create a point cloud from a disparity image and a focal length.

    Arguments:
      disparity_image: disparities in pixels.
      image_left: BGR-format left stereo image, to color the points.
      focal_length: the focal length of the stereo camera, in pixels.

    Returns:
      A string containing a PLY point cloud of the 3D locations of the
        pixels, with colors sampled from left_image. You may filter low-
        disparity pixels or noise pixels if you choose.
    """

    w, h = disparity_image.shape
    Q = np.float32([[1, 0, 0, -0.5*w],
                    [0, -1, 0,  0.5*h],  # turn points 180 deg around x-axis,
                    [0, 0, focal_length,     0],  # so that y-axis looks up
                    [0, 0, 0,      1]])
    points = cv2.reprojectImageTo3D(disparity_image, Q)
    colors = cv2.cvtColor(image_left, cv2.COLOR_BGR2RGB)
    mask = disparity_image > disparity_image.min()
    out_points = points[mask]
    out_colors = colors[mask]

    output = StringIO.StringIO()

    verts = np.hstack([out_points, out_colors])
    output.write(ply_header % dict(vert_num=len(verts)))
    np.savetxt(output, verts, '%f %f %f %d %d %d')

    return output.getvalue()


ply_header = '''ply
format ascii 1.0
element vertex %(vert_num)d
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
'''


def main():
    import sys
    if len(sys.argv) < 5:
        print """Usage: ./stereo.py [output_point_cloud]
                 [left_image] [right_image] [focal_length]
                 [window size] [min disparity] [uniqueness ratio]"""
        return

    out_file = sys.argv[1]
    image_left = cv2.imread(sys.argv[2])
    image_right = cv2.imread(sys.argv[3])
    focal_length = sys.argv[4]

    fmat, h_left, h_right = rectify_pair(image_left, image_right)

    left_h, left_w, _ = image_left.shape
    left_shape = (left_w, left_h)
    rectify_left = cv2.warpPerspective(image_left, h_left, left_shape)

    right_h, right_w, _ = image_right.shape
    right_shape = (right_w, right_h)
    rectify_right = cv2.warpPerspective(image_right, h_right, right_shape)

    disparity = my_disparity_map(
        rectify_left, rectify_right,
        int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]))

    ply_string = point_cloud(disparity, image_left, focal_length)

    with open(out_file, 'w') as f:
        f.write(ply_string)

    cv2.imshow("left", image_left)
    cv2.imshow("right", image_right)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imshow("rleft", rectify_left)
    cv2.imshow("rright", rectify_right)
    cv2.imshow("disparity", disparity)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def my_disparity_map(
        image_left, image_right, window_size_, min_disp_, uniquenessRatio_):
    """Compute the disparity images for image_left and image_right.

    Arguments:
      image_left, image_right: rectified stereo image pair.

    Returns:
      an single-channel image containing disparities in pixels,
        with respect to image_left's input pixels.
    """
    window_size = window_size_
    min_disp = min_disp_
    num_disp = 112-min_disp
    stereo = cv2.StereoSGBM(
        minDisparity=min_disp,
        numDisparities=num_disp,
        SADWindowSize=window_size,
        uniquenessRatio=uniquenessRatio_,
        speckleWindowSize=0,
        speckleRange=0,
        disp12MaxDiff=1,
        P1=8*3*window_size**2,
        P2=32*3*window_size**2,
        fullDP=False
        )

    disp_1 = stereo.compute(image_left, image_right) / 16
    disp_1 = np.array(disp_1, dtype='uint8')

    return disp_1


if __name__ == '__main__':
    main()
