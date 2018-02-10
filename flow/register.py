import sys
from sklearn.linear_model import LinearRegression
from reportlab.lib.units import inch
from skimage import measure
from flow.models import *
from params import *
import numpy as np
import cv2

def points2paper (points):
    return [(x * SCAN_PPI/inch, y * SCAN_PPI/inch) for x, y in points]

def boxes2paper (boxes):
    return [(x * SCAN_PPI / inch,
            y * SCAN_PPI / inch,
            w * SCAN_PPI / inch,
            h * SCAN_PPI / inch)
            for x, y, w, h in boxes]

def expand (box, shape, l):
    y0, x0, y1, x1 = box
    H, W = shape
    y0 = max(0, y0-l)
    x0 = max(0, x0-l)
    y1 = min(H, y1+l)
    x1 = min(W, x1+l)
    return y0, x0, y1, x1

def detect_center (patch):
    cv2.imwrite('xxx.png', patch)
    # detect outer circle
    circles = cv2.HoughCircles(patch, cv2.HOUGH_GRADIENT, 1, 1000, param1=50,param2=30, minRadius=30, maxRadius=60)
    if circles is None:
        return None
    outside = circles[0, 0, :]
    #print("outside circle", outside)

    # remove outside circle 
    H, W = patch.shape
    mask = np.ones((H, W), dtype=np.uint8)
    x, y, r = np.round(outside).astype("int")
    cv2.circle(mask, (x, y), r * 4 //5, 0, -1)
    patch[mask > 0] = 0
    # detect inside circle
    circles = cv2.HoughCircles(patch, cv2.HOUGH_GRADIENT, 1, 1000, param1=50,param2=30, minRadius=0, maxRadius=0)
    if circles is None:
        return None
    inside = circles[0, 0, :]
    #print("inside circle", inside)

    '''
    patch = cv2.cvtColor(patch, cv2.COLOR_GRAY2BGR)
    cv2.circle(patch, (x, y), r, (0, 255, 0), 4)
    x, y, r = np.round(inside).astype("int")
    cv2.circle(patch, (x, y), r, (0, 255, 0), 4)
    '''

    x1, y1, _ = outside
    x2, y2, _ = inside

    return (x1+x2)/2, (y1+y2)/2

def detect_circles (gray, off):
    #image = cv2.GaussianBlur(gray, (9, 9), 0)
    binary = gray < BLACK_TH
    labels = measure.label(binary, background=0)

    #cv2.imwrite('xxx.png', binary * 255)
    #sys.exit(0)
    H, W = binary.shape

    centers = []
    X0, Y0 = off
    for box in measure.regionprops(labels):
        if box.area < 2000:
            continue
        #print(box.bbox)
        y0,x0,y1,x1 = expand(box.bbox, binary.shape, 10)
        
        patch = gray[y0:y1, x0:x1]

        x, y = detect_center(patch)
        
        #print("\t", box.area, box.centroid)
        centers.append([X0+x0+x, Y0+y0+y])
    return centers

def detect_anchors (gray):
    H, W = gray.shape
    if H > W:
        h = H//4
        w = W//7
    else:
        h = H//7
        w = W//4

    blocks = [(0, 0),
              (W-w, 0),
              (0, H-h),
              (W-w, H-h)]
    anchors = []
    for i, (x, y) in enumerate(blocks):
        aoi = np.copy(gray[y:(y+h), x:(x+w)])
        cv2.imwrite('block-%d.png' % i , aoi)
        circles = detect_circles(aoi, (x, y))

        if H > W:   # portrait
            circles.sort(key=lambda a: a[1])
        else:       # landscape
            circles.sort(key=lambda a: a[0])
        anchors.append(circles)
        pass
    return anchors

def rotate_clockwise (image):
    image = cv2.transpose(image)
    return cv2.flip(image, 1)

def rotate_counterclockwise (image):
    image = cv2.transpose(image)
    return cv2.flip(image, 0)

def rotate_normalize (image):
    anchors = detect_anchors(image)
    print([len(x) for x in anchors])
    if len(anchors[1]) == 5:
        return rotate_clockwise
    elif len(anchors[2]) == 5:
        return rotate_counterclockwise
    pass


def calibrate (image, layout):
    anchors = detect_anchors(image)
    assert len(anchors[3]) == 5
    X = np.array(sum(anchors, []), dtype=np.float32)
    gs_anchors = points2paper(layout.anchors)
    y1 = np.array([x for x , _ in gs_anchors], dtype=np.float32)
    y2 = np.array([y for _ , y in gs_anchors], dtype=np.float32)
    reg_x = LinearRegression()
    reg_y = LinearRegression()
    reg_x.fit(X, y1)
    print("SCORE X:", reg_x.score(X, y1))
    reg_y.fit(X, y2)
    print("SCORE Y:", reg_x.score(X, y2))
    #print(reg_x.coef_, reg_x.intercept_)
    #print(reg_y.coef_, reg_y.intercept_)
    affine = np.zeros((2,3), dtype=np.float32)
    affine[0, :2] = reg_x.coef_
    affine[0, 2] = reg_x.intercept_
    affine[1, :2] = reg_y.coef_
    affine[1, 2] = reg_y.intercept_
    return affine

def bbox1(img):
    a = np.where(img > 0)
    bbox = np.min(a[0]), np.max(a[0]), np.min(a[1]), np.max(a[1])
    return bbox

def bbox2(img):
    rows = np.sum(img, axis=1)
    cols = np.sum(img, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return rmin, cmin, rmax+1, cmax+1

def crop_margin (image, gray):
    black = gray < BLACK_TH
    y0, x0, y1, x1 = expand(bbox2(black), black.shape, 20)
    return image[y0:y1, x0:x1], gray[y0:y1, x0:x1]

def normalize (image, layout):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    image, gray = crop_margin(image, gray)

    rotate = rotate_normalize(gray)
    image = rotate(image)
    gray = rotate(gray)

    affine = calibrate(gray, layout)

    W, H = layout.paper_size
    W = int(round(W * SCAN_PPI / inch))
    H = int(round(H * SCAN_PPI / inch))

    return cv2.warpAffine(image, affine, (W, H))


