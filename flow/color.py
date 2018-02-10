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
    H[H < HUE_TH] = 0
    H[S < SAT_TH] = 0
    S[S < SAT_TH] = 0
    V[:,:] = 255
    return hsv

def hue (image):
    return hsv(image)[:, :, 0]

def filter_color (image):
    #if not colormap is None:
    #    gen_colormap(colormap, H, S)
    return cv2.cvtColor(hsv(image), cv2.COLOR_HSV2BGR)

class PixelClassifier:
    def __init__ (self):
        self.classes = []
        pass

    def fit (self, samples):
        classes = []
        for sample in samples:
            h = hue(sample)
            # count number of pixels
            nc = np.sum(h > 0)
            cc = np.sum(h) / nc
            h[np.abs(h - cc) > CLASS_GAP] = 0
            nc = np.sum(h > 0)
            cc = np.sum(h) / nc
            if nc > LEGEND_TH:
                print("COLOR DETECTED:", cc, nc)
                classes.append(cc)
                pass
        classes.sort()
        for i in range(1, len(classes)):
            assert classes[i] - classes[i-1] > 2 * (CLASS_GAP + CLASS_RELAX)
        self.classes = classes
        pass

    def predict (self, image):
        r = []
        h = hue(image)
        for cc in self.classes:
            binary = (np.abs(h - cc) < CLASS_GAP)
            binary = morphology.remove_small_objects(binary, SMALL_OBJECT)
            r.append(binary)
            pass
        return r

