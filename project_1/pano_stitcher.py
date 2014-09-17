"""Project 1: Panorama stitching.

In this project, you'll stitch together images to form a panorama.

A shell of starter functions that already have tests is listed below.

TODO: Implement!
"""

import cv2
import numpy as np


def homography(image_a, image_b):
    """Returns the homography mapping image_b into alignment with image_a.

    Arguments:
      image_a: A grayscale input image.
      image_b: A second input image that overlaps with image_a.

    Returns: the 3x3 perspective transformation matrix (aka homography)
             mapping points in image_b to corresponding points in image_a.
    """
    sift = cv2.SIFT()

    # find features and descriptors
    kp1, des1 = sift.detectAndCompute(image_a, None)
    kp2, des2 = sift.detectAndCompute(image_b, None)

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # store good matches
    best_matches = []
    for x, y in matches:
        if x.distance < 0.75 * y.distance:
            best_matches.append(x)
    src_pts = np.float32([kp1[m.queryIdx].pt for m in best_matches])
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in best_matches])

    M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
    if(len(best_matches) <= 100):
        return np.eye(3,3)
    else:
        return M

    pass


def warp_image(image, homography):
    """Warps 'image' by 'homography'

    Arguments:
      image: a 3-channel image to be warped.
      homography: a 3x3 perspective projection matrix mapping points
                  in the frame of 'image' to a target frame.

    Returns:
      - a new 4-channel image containing the warped input, resized to contain
        the new image's bounds. Translation is offset so the image fits exactly
        within the bounds of the image. The fourth channel is an alpha channel
        which is zero anywhere that the warped input image does not map in the
        output, i.e. empty pixels.
      - an (x, y) tuple containing location of the warped image's upper-left
        corner in the target space of 'homography', which accounts for any
        offset translation component of the homography.
    """
    rows, cols, _ = image.shape
    rows *= int(homography[0][0])
    cols *= int(homography[1][1])
    img = cv2.warpPerspective(image, homography, (cols, rows))
    return img, (homography[0][2], homography[1][2])

    pass

def stitch(img1, img2, homo):
  rows1, cols1, _ = img1.shape
  rows2, cols2, _ = img2.shape
  ret_image = np.zeros((rows1+rows2, cols1+cols2, 4), np.uint8)

  for i in range(rows1):
      for j in range(cols1):
          ret_image[i][j] = img1[i][j]
  
  for i in range(rows2):
      for j in range(cols2):
          ret_image[i+homo[1][2]][j+homo[0][2]] = img2[i][j]

  return ret_image

def create_mosaic(images, origins):
    """Combine multiple images into a mosaic.

    Arguments:
      images: a list of 4-channel images to combine in the mosaic.
      origins: a list of the locations upper-left corner of each image in
               a common frame, e.g. the frame of a central image.

    Returns: a new 4-channel mosaic combining all of the input images. pixels
             in the mosaic not covered by any input image should have their
             alpha channel set to zero.
    """
    images = list(images)
    sift = cv2.SIFT()
    st_img = images[0]
    print images[0]
    del images[0]
    
    s = len(images)
    i = 0

    while(i < s):
      print i
      img = images[0]
      del images[0]
      m = homography(st_img, img)
      if(not np.array_equal(m, np.eye(3,3))):
        st_img = stitch(st_img, img, m)
        i += 1
      else:
        images.append(img)        

    '''
    for i in range(len(images[1:])):
      print i
      m = homography(st_img, images[i])
      if(not np.array_equal(m,np.eye(3,3))):
          st_img = stitch(st_img, images[i], m)
      else:
        images.append(images[i])
    '''
    '''
    for i in range(len(images)):
      for j in range(len(images)):
        if(i != j):
          m = homography(images[i],images[j])
          if(not np.array_equal(m,np.eye(3,3))):
              st_img = stitch(images[i], images[j], m)
              cv2.imwrite("test.png", st_img)
              exit()
          else:
            print "FOUND EYE!!"
    '''
    cv2.imwrite("test.jpg", st_img)
    return st_img
    pass
