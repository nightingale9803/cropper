import cv2 as cv
import numpy as np
from math import *
from PIL import Image


# a quick and simple version of RGBA outline extractor and masking using invert mask
def convert_alpha(masked, outline):
    # create a blank rgba canvas with transparent background
    # mask the canvas with the outline with black untransparent bg (inverted mask)
    # let the alpha channel of invert masked image also be 0
    # concatenate the masked and the rgba canvas
    rgba_canvas = np.zeros((masked.shape[0], masked.shape[1], 4), dtype=np.uint8) + 255
    rgba_canvas[:, :, 3] = 0
    cv.fillPoly(rgba_canvas, [outline], (0, 0, 0, 255))
    # if the input is a gray image, convert it to rgba
    if len(masked.shape) == 2:
        masked2 = cv.cvtColor(masked, cv.COLOR_GRAY2RGBA)
    # if is rgb, convert it to rgba
    elif len(masked.shape) == 3 and masked.shape[2] == 3:
        masked2 = cv.cvtColor(masked, cv.COLOR_RGB2RGBA)
    # if is rgba, do nothing
    elif len(masked.shape) == 3 and masked.shape[2] == 4:
        masked2 = masked
    masked2[:, :, 3] = 0  # change alpha channel to 0
    new = cv.add(rgba_canvas, masked2)
    return new


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

    def __init__(self, img_input, threshold=(200, 150), mode="poly", padding="white"):
        self.mode = mode
        # read image into grayscale ndarray
        if type(img_input) == str:
            try:
                self.original = np.array(Image.open(img_input))
                image = np.array(Image.open(img_input).convert("L"))
            except FileNotFoundError:
                raise FileNotFoundError(
                    "Image file not found, make sure the path to the image is correct"
                )
        elif type(img_input) == Image.Image:
            self.original = np.array(img_input)
            image = np.array(img_input.convert("L"))
        elif type(img_input) == np.ndarray:
            self.original = img_input
            image = img_input
        else:
            raise ValueError(
                "Invalid input image type, must be a path string, PIL Image, or numpy array"
            )
        self.gray = image
        # erode by a large kernel to merge smaller bounding boxes to cut computation, and to distinguish the tracing outlines
        self.eroded = cv.erode(self.gray, np.ones((21, 21), np.uint8), iterations=1)
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
            3. Width/Height ratio, should not exceed 5 to filter out the title text and others. Could consider crop the title text before processing if needed.
            4. (Optional, not implemented) Extent ratio of the contour area to the bounding rectangle area. Normally the width and height will suffice, but it might be hard to find the correct value and some bones might be very small. So, in that case, can consider use shape descriptors, as Text, being more block-like and rectangle-like, might have a higher extent ratio compared to irregular bone tracings.
        """
        # can also consider use NMS suppression algorithm to merge adjancent boxes, it might not be necessary in our case as text boxes are merged by erosion and bone tracings are singular

        # also make distinction between RGB and Gray images, where first-level contours have different parent index behavior
        if len(self.original.shape) == 3:
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
            if len(valid_contours) == 0:
                valid_contours = [
                    cnt
                    for i, cnt in enumerate(contours)
                    if hierarchy[0][i][3] == -1
                    and (
                        cv.boundingRect(cnt)[2] > threshold[0]
                        or cv.boundingRect(cnt)[3] > threshold[1]
                    )
                    and cv.boundingRect(cnt)[2] / cv.boundingRect(cnt)[3] < 5
                ]
        else:
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
            # give an extra 15% space around the new images, can add more if needed
            cropped = convert_alpha(self.original, cnt)
            cropped = cropped[y : y + h, x : x + w]
            if padding == "transparent":
                padding_value = (255, 255, 255, 0)
            elif padding == "black":
                padding_value = (0, 0, 0, 255)
            else:
                padding_value = (255, 255, 255, 255)
            cropped = cv.copyMakeBorder(
                cropped,
                int(h * 0.15),
                int(h * 0.15),
                int(w * 0.15),
                int(w * 0.15),
                cv.BORDER_CONSTANT,
                value=padding_value,
            )
            # detect original image's shape and save the cropped image as either Gray, RGB, or RGBA
            # if is transparent
            if padding == "transparent":
                cropped = cropped
            else:
                # if is gray
                if len(self.original.shape) == 2:
                    cropped = cv.cvtColor(cropped, cv.COLOR_RGBA2GRAY)
                # if is rgb
                elif len(self.original.shape) == 3 and self.original.shape[2] == 3:
                    cropped = cv.cvtColor(cropped, cv.COLOR_RGBA2RGB)
                # if is rgba
                elif len(self.original.shape) == 3 and self.original.shape[2] == 4:
                    cropped = cropped
            imgs.append(cropped)
            # replace the original page image with white background where the bone tracings are
            self.gray[mask == 0] = 255
        output["images"] = imgs
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
