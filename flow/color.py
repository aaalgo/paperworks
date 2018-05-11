import numpy as np
import cv2
from skimage import morphology
from params import *

def gen_colormap (path, H, S):
    L=500
    vis = np.zeros((L,L,3), dtype=np.float32)
    Y, X = H.shape
    for i in range(Y):
        h = H[i]
        s = S[i]
        for j in range(X):
            vh = int(round(h[j] * (L-1)/360))
            vs = int(round(s[j] * (L-1)))
            vis[vh,vs,0] = h[j]
            vis[vh,vs,1] = s[j]
            pass
        pass
    vis[:,:,2] = 255.0
    hsv = cv2.cvtColor(vis, cv2.COLOR_HSV2BGR)
    cv2.imwrite(path, hsv)

def hsv (image):
    inf = np.clip((image.astype(np.float32) + BRIGHTEN), 0, 255)
    hsv = cv2.cvtColor(inf, cv2.COLOR_BGR2HSV)
    H = hsv[:,:,0]
    S = hsv[:,:,1]
    V = hsv[:,:,2]
    #H[H < HUE_TH] = 0
    #H[S < SATURATE_TH] = 0
    S[S < SATURATE_TH] = 0
    V[:,:] = 255
    return hsv #[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

def split_hsv (hsv):
    return hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

def filter_color (image):
    #if not colormap is None:
    #    gen_colormap(colormap, H, S)
    return cv2.cvtColor(hsv(image), cv2.COLOR_HSV2BGR)

def dist_mod360 (h, cc):    # center cc
    return np.minimum(np.minimum(np.abs(h-cc), np.abs(h-360-cc)), np.abs(h+360-cc))

def detect_color (h, invalid_mask):

    h0 = np.copy(h)
    h0[h0 > 180] -= 360

    mh = np.ma.masked_array(h, mask=invalid_mask)
    mh0 = np.ma.masked_array(h0, mask=invalid_mask)

    if mh0.std() < mh.std():
        print('RED DETECTED')
        h = h0
        mh = mh0

    cc = mh.mean()

    bad = dist_mod360(h, cc) > CLASS_GAP

    invalid_mask = np.logical_or(bad, invalid_mask)

    nc = np.sum(np.logical_not(invalid_mask))
    cc = np.ma.masked_array(h, mask=invalid_mask).mean()

    return cc, nc

class PixelClassifier:
    def __init__ (self):
        self.classes = []
        pass

    def fit (self, samples):
        classes = []
        for sample in samples:
            h, s, _ = split_hsv(hsv(sample))
            # count number of pixels

            cc, nc = detect_color(h, s < SATURATE_TH)

            if not (nc >= SAMPLE_TH):
                continue
            print("COLOR DETECTED:", cc, nc)
            classes.append(cc)
            pass
        classes.sort()
        print('COLORS:', classes)
        for i in range(1, len(classes)):
            assert classes[i] - classes[i-1] > 2 * (CLASS_GAP + CLASS_RELAX)
        self.classes = classes
        pass

    def predict (self, image):
        r = []
        h, s, _ = split_hsv(hsv(image))
        for cc in self.classes:
            binary = np.logical_and(dist_mod360(h, cc) < CLASS_GAP, s >= SATURATE_TH)
            binary = morphology.remove_small_objects(binary, SMALL_OBJECT)
            r.append(binary)
            pass
        return r

