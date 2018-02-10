from django.db import models
import numpy as np
import cv2
from params import *

class Page (models.Model):
    done = models.BooleanField(default = False)
    pass

class Image (models.Model):
    path = models.CharField(max_length=2500)
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True)
    width = models.IntegerField()
    height = models.IntegerField()
    page_x = models.FloatField(null=True)
    page_y = models.FloatField(null=True)
    page_w = models.FloatField(null=True)
    page_h = models.FloatField(null=True)
    rotate = models.BooleanField(default=False)

    def embed_path (self, rotate):
        if rotate:
            return 'embed/%d-r.png' % self.id
        return 'embed/%d.png' % self.id

    def gen_embed (self):
        image = cv2.imread(self.path, cv2.IMREAD_GRAYSCALE)
        mean = np.mean(image)
        if mean < 128:
            image = 255 - image
        image = cv2.normalize(image, None, MIN_COLOR, 255, cv2.NORM_MINMAX)
        image = cv2.flip(image, 0)
        cv2.imwrite(self.embed_path(False), image)
        cv2.imwrite(self.embed_path(True), cv2.transpose(image))
    pass

class Batch (models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    pass

class BatchPage (models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True)
    page = models.ForeignKey(Page, on_delete=models.PROTECT, null=True)
    pass

class Scan (models.Model):
    path = models.CharField(max_length=2500, unique=True)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, null=True)
    page = models.ForeignKey(Page, on_delete=models.PROTECT, null=True)


