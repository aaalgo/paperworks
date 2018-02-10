Paperworks - Image Annotation with Paper and Markers
====================================================

# Introduction

## [PDF](doc/pdf.jpg)	

## [marker](doc/marker.jpg)

## [scan](doc/scan.jpg)

## [transform](doc/color.jpg)

## [mask](doc/mask.gif)

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

