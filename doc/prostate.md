Paperworks Demo: Prostate MRI Image Annotation
==============================================

# 1. Input Images

The input images are from
[TCIA PROSTATEx](https://wiki.cancerimagingarchive.net/display/Public/SPIE-AAPM-NCI+PROSTATEx+Challenges#935fa28f51c546c588e892026a1396c6) dataset.

![image1](http://www.aaalgo.com/demos/paperworks/prostate/images/ProstateX-00003-t2tsesag-87368.png)
![image2](http://www.aaalgo.com/demos/paperworks/prostate/images/ProstateX-00014-t2tsesag-22089.png)

[Browse All Images](http://www.aaalgo.com/demos/paperworks/prostate/images/)

# 2. Task Generation

The 372 images are tiled and organized into 62 PDF pages.
These PDF pages are divided into 4 PDF job files, each with 20 pages at
most.

[Browse Task PDF files](http://www.aaalgo.com/demos/paperworks/prostate/jobs/)

# 3. Hand Annotation and Scanning

The job files are printed and hand-annotated with color markers.
The pages are then scanned.  Scanning can be done in any order or
orientation; paperworks automatically registers the images by 
barcode and by the anchor circles.

Sample scanned file in low-resolution:

![scan0](http://www.aaalgo.com/demos/paperworks/prostate/scan/out0.jpg)
![scan1](http://www.aaalgo.com/demos/paperworks/prostate/scan/out1.jpg)


[Browse Sample TIFF Files](http://www.aaalgo.com/demos/paperworks/prostate/scan/)

# 4. Post Processing

## Extraction of colors
![colors](http://www.aaalgo.com/demos/paperworks/prostate/246-color.png)

## Split Into Color Channels

The color samples in the sample boxes (grayscale rectangles outside the
images) are collected and used to categorize colors.

![ch1](http://www.aaalgo.com/demos/paperworks/prostate/246-0.png)
![ch2](http://www.aaalgo.com/demos/paperworks/prostate/246-1.png)
![ch3](http://www.aaalgo.com/demos/paperworks/prostate/246-2.png)

These color channels are then mapped back to the original images and
used to generate the annotation masks.

[Browse All Intermediate Files](http://www.aaalgo.com/demos/paperworks/prostate/aligned/)

# 5. Mask Files Produced

All detected colors are assigned an ID 1, 2, 3.  Mask file pixel values
are color IDs.  Small false positive regions are visible from the images
below.  These can be removed by post-processing, or by setting
`SMALL_OBJECT` threshold in the `params.py`.

![mask1](http://www.aaalgo.com/demos/paperworks/prostate/aligned/vis-100.gif)
![mask1](http://www.aaalgo.com/demos/paperworks/prostate/aligned/vis-101.gif)

[Browse Mask Files](http://www.aaalgo.com/demos/paperworks/prostate/masks/)

