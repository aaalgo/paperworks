#!/usr/bin/env python
import sys
import cv2
import zbar


image = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
small = cv2.resize(image, None, fx=0.4, fy=0.4)
scanner = zbar.ImageScanner()
H, W = small.shape
zimage = zbar.Image(W, H, 'Y800', small.tostring())
scanner.scan(zimage)
for symbol in zimage:
    #print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data
    print(symbol.data)
    break
