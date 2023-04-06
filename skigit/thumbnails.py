import os
import sys
from PIL import Image, ImageFilter
import logging

logger = logging.getLogger('Skigit')

class SkigitThumbnail:
    """
    SkigitThumbnail class takes care of generating thumbnails from original image size
    """

    THUMBNAIL_ORIGINAL_FOLDER = "image_raw/"
    THUMBNAIL_PUBLIC_FOLDER   = "thumbnails/"
    THUMBNAIL_FORMAT          = "JPEG"
    THUMBNAIL_BLUR            = 50
    THUMBNAIL_WIDTH           = 480
    THUMBNAIL_HEIGHT          = 360

    def __init__(self, image_raw_path=None):
        self.input_path = image_raw_path
        self.generate()
        
    def get_gaussian_background(self):
        blrd = self.image_raw.filter(ImageFilter.GaussianBlur(self.THUMBNAIL_BLUR))
        rszd = blrd.resize((self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT))
        return rszd

    def get_thumbnail(self):
        cp = self.image_raw.copy()
        cp.thumbnail((self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT))
        return cp

    def get_thumbnail_background(self, blurBackground):
        dst = Image.new('RGB', (blurBackground.width, blurBackground.height))
        dst.paste(blurBackground, (0, 0))
        dst.paste(self.image_thumbnail, ((blurBackground.width - self.image_thumbnail.width)//2, (blurBackground.height - self.image_thumbnail.height)//2))
        return dst

    def generate(self):
        try:
            with Image.open(self.input_path) as im:
                self.image_raw = im
                self.image_thumbnail = self.get_thumbnail()
                bg = self.get_gaussian_background()
                self.image_thumbnail = self.get_thumbnail_background(bg)
        except Exception as exc:            
            logger.error("Thumbnail Generation Exception", exc)

    def save_thumbnail(self, output_path):
        try:
            self.output_path = output_path.lower()
            self.image_thumbnail.save(self.output_path, self.THUMBNAIL_FORMAT)
        except Exception as exc:
            logger.error("Thumbnail Saving Exception", exc)


    def remove_local_thumbnail(self):
        try:   
            os.remove(self.output_path)        
            self.output_path = None
        except Exception as exc:            
            logger.error("Thumbnail Delete Exception", exc)

