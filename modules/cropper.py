import cv2 as cv
import numpy as np
from math import *
from PIL import Image


class RubbingCropper:
    """
    description:
      A class for cropping bone tracings from an image input as seperate local files, and replace the bone contours with a white background, leaving only the numbers behind

    args:
      img_input: str, PIL Image, or numpy array
      threshold: tuple, (int, int), the threshold for distinguishing the text and the bone, in width and height, those smaller than the threshold will be considered a number text
      mode: str, "rect" or "poly", the mode of cropping the bone tracings, "rect" will use the bounding rectangle of the contours, "poly" will use the polygon outline of the contours. Polygon will result in much higher precision cropping, however, it has problems with open contours. Rects is a better choice here.

    attribute:
      gray: the grayscale image of the original page
      eroded: the eroded grayscale image
      binary: the binarzied image
      output:
        {dict}:
          [bones]: image files as a list of numpy arrays
          [boxes]: the bounding boxes of the bone tracings
          [page]: the original image with bone tracings replaced by white background
    """

    def __init__(self, img_input, threshold=(200, 150), mode="poly"):
        self.mode = mode
        # read image into grayscale ndarray
        if type(img_input) == str:
            try:
                image = np.array(Image.open(img_input).convert("L"))
            except FileNotFoundError:
                raise FileNotFoundError(
                    "Image file not found, make sure the path to the image is correct"
                )
        elif type(img_input) == Image.Image:
            image = np.array(img_input.convert("L"))
        elif type(img_input) == np.ndarray:
            image = img_input
        else:
            raise ValueError(
                "Invalid input image type, must be a path string, PIL Image, or numpy array"
            )
        self.gray = image
        # erode by a large kernel to merge smaller bounding boxes to cut computation, and to distinguish the tracing outlines
        self.eroded = cv.erode(self.gray, np.ones((23, 23), np.uint8), iterations=1)
        # a simple thresholding will do， as the image quality is quite good, otherwise, consider Canny instead
        self.binary = cv.threshold(
            self.eroded, 127, 255, cv.THRESH_BINARY + cv.THRESH_OTSU
        )[1]
        contours, hierarchy = cv.findContours(
            self.binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
        )
        """
          Following code get only the first level bone contours, and filter out the number texts. This are several considerations:
            1. parent-child relationship in the hierarchy, only first level should be found, thus filtering out all oracle bone characters
            2. contour width and height. Use a (width, height) threshold to tell between the bone tracings and the number texts. The condition should be "and" or "or". The "or" might work better.Though the title text must be filtered out. This can be done by examining height/width ratio.
            3. Width/Height ratio, should not exceed 5 to filter out the title text "甲骨摹本大系" and others. Could consider crop the title text before processing if needed.
            4. (Optional, not implemented) Extent ratio of the contour area to the bounding rectangle area. Normally the width and height will suffice, but it might be hard to find the correct value and some bones might be very small. So, in that case, can consider use shape descriptors, as Text, being more block-like and rectangle-like, might have a higher extent ratio compared to irregular bone tracings.
        """
        # can also consider use NMS suppression algorithm to merge adjancent boxes, it might not be necessary in our case as text boxes are merged by erosion and bone tracings are singular
        valid_contours = [
            cnt
            for i, cnt in enumerate(contours)
            if hierarchy[0][i][3] == 0
            and (
                cv.boundingRect(cnt)[2] > threshold[0]
                or cv.boundingRect(cnt)[3] > threshold[1]
            )
            and cv.boundingRect(cnt)[2] / cv.boundingRect(cnt)[3] < 5
        ]
        # merge the child boxes manually in case the tracing outline is not closed
        valid_contours = self.merge_nested_contours(valid_contours)
        self.contours = valid_contours  # for debugging
        output = {}
        imgs = []
        # crop the bone tracings by their polygon outline rather than rectangles
        for i, cnt in enumerate(valid_contours):
            # this is done by cropping image by binary masks
            mask = np.full_like(
                self.gray, 255
            )  # use full_like rather than zeros_like to create white background
            if self.mode == "poly":
                cv.drawContours(mask, [cnt], -1, 0, -1)
            else:
                x, y, w, h = cv.boundingRect(cnt)
                cv.rectangle(mask, (x, y), (x + w, y + h), 0, -1)
            # Find the bounding rectangle of the contour
            x, y, w, h = cv.boundingRect(cnt)
            cropped = np.full_like(self.gray, 255)
            # can erode mask if extra space around the tracing is needed
            cropped[mask == 0] = self.gray[mask == 0]
            cropped = cropped[y : y + h, x : x + w]
            # give an extra 15% space around the new images, can add more if needed
            cropped = cv.copyMakeBorder(
                cropped,
                int(h * 0.15),
                int(h * 0.15),
                int(w * 0.15),
                int(w * 0.15),
                cv.BORDER_CONSTANT,
                value=(255, 255, 255),
            )
            imgs.append(cropped)
            # replace the original page image with white background where the bone tracings are
            self.gray[mask == 0] = 255
        output["bones"] = imgs
        output["page"] = self.gray
        output["boxes"] = [cv.boundingRect(cnt) for cnt in valid_contours]
        self.output = output

    def merge_nested_contours(self, contours):
        """
        This function is designed to merge nested boxes if any, this might happen when the bone tracings are not completely closed. I currently have no idea how to close the contour manually as some of the open contours are broken in the middle and will not close no matter what.
        """
        boxes = [cv.boundingRect(cnt) for cnt in contours]
        to_remove = []
        for i, box in enumerate(boxes):
            for j, other_box in enumerate(boxes):
                if i != j:
                    if (
                        box[0] <= other_box[0]
                        and box[1] <= other_box[1]
                        and box[0] + box[2] >= other_box[0] + other_box[2]
                        and box[1] + box[3] >= other_box[1] + other_box[3]
                    ):
                        to_remove.append(j)
        merged = [cnt for i, cnt in enumerate(contours) if i not in to_remove]
        return merged
