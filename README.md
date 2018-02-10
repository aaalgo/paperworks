Paperworks - Image Annotation with Paper and Markers
====================================================

# Introduction

## Import images and generate PDF.
The software tries to pack multiple images into single pages
whenever possible.
![PDF](doc/pdf.jpg)	

## Annotate with markers.
![marker](doc/marker.jpg)

## Scan.
![scan](doc/scan.jpg)

## Registration.
![transform](doc/color.jpg)

## Masks.
![mask](doc/mask.gif)

# Prerequisites
```
apt-get install zbar-tools
pip install reportlab scikit-learn scikit-image django imageio opencv-python
```

# Workflow

1. Checkout source code
```
git clone https://github.com/aaalgo/paperworks
cd paperworks
```

2. Put images to `paperwors/images`

3. Generate PDF tasks

4. Print and annotate with markers

5. Scan images to `paperworks/scan/*.tiff`

Recommended configuration is 24-bit color with resolution = 200.

6. Process and generate masks
```
./manage.py scan
```
Some visualizations will be produced in `paperworks/aligned`, and for
each input image there will be a `*.png` file.  The pixel values of the
mask file are 1, 2, ..., each corresponding to a different color used.


# Tips

- Use red and blue, or red, blue and green.


# 

