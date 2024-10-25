from math import *
from PIL import Image
import numpy as np
import os, sys
import pdfplumber

import argparse
from tqdm import tqdm

# import local modules
sys.path.append("..")
from modules.cropper import RubbingCropper


def parse_pdf(
    src_path,
    save_path,
    mode="poly",
    padding="white",
    start_page=1,
    end_page=-1,
    dpi=600,
    text_threshold=(200, 100),
    only_object=True,
):
    """
    description:
      main wrapper function for parsing a pdf
    args:
      src_path: str, path to pdf file or folder containing images to be parsed.
      save_path: str, path to the output folder, the folder will be created if not exist.
      exclude_range: list, list of page numbers to exclude from parsing.
      dpi: int, resolution of the image to be saved.
    """
    if os.path.isfile(src_path) and src_path.endswith(".pdf"):
        with pdfplumber.open(src_path) as pdf:
            print(f"Processing begins for {len(pdf.pages)} pages...")
            for i, page in enumerate(tqdm(pdf.pages)):
                if i < start_page - 1:
                    print(f"page {start_page} excluded, continue...")
                    continue
                if end_page != -1 and i >= end_page:
                    print(f"specified end page {end_page} reached, stop processing...")
                    break
                page_num = page.page_number
                img = page.to_image(
                    resolution=dpi, antialias=True
                )  # abbyy finereader image conversion use a 600dpi, consider chaning this if needed
                page.close()  # release memory
                # get all the bone tracings and page with bone tracings replaced by white background, see other file for details of the class
                output = RubbingCropper(
                    img.original, text_threshold, mode=mode, padding=padding
                ).output
                for j, bone in enumerate(output["images"]):
                    box = output["boxes"][j]
                    save_name = f"{page_num}-{[box[0], box[1], box[2], box[3]]}.png"
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    if not os.path.exists(os.path.join(save_path, "images")):
                        os.makedirs(os.path.join(save_path, "images"))
                    if not only_object and not os.path.exists(
                        os.path.join(save_path, "pages")
                    ):
                        os.makedirs(os.path.join(save_path, "pages"))
                    # save the bone tracings
                    Image.fromarray(bone).save(
                        os.path.join(save_path, "images", save_name), dpi=(dpi, dpi)
                    )
                    # save the page with bone tracings replaced by white background
                    if not only_object:
                        Image.fromarray(output["page"]).save(
                            os.path.join(save_path, "pages", f"{page_num}.png"),
                            dpi=(dpi, dpi),
                        )
            print(f"Processing finished!")
    else:
        # if is file and ends with image extension
        if os.path.isfile(src_path) and (
            src_path.endswith(".png")
            or src_path.endswith(".jpg")
            or src_path.endswith(".jpeg")
            or src_path.endswith(".tif")
            or src_path.endswith(".tiff")
            or src_path.endswith(".bmp")
            or src_path.endswith(".webp")
        ):
            images = [src_path]
        elif os.path.isdir(src_path):
            # get all the images in the folder
            images = [
                os.path.join(src_path, f)
                for f in os.listdir(src_path)
                if f.endswith(".png")
                or f.endswith(".jpg")
                or f.endswith(".jpeg")
                or f.endswith(".tif")
                or f.endswith(".tiff")
                or f.endswith(".bmp")
                or f.endswith(".webp")
            ]
        else:
            print(
                "Invalid input path, the path should be a pdf or an image or a folder containing images."
            )
            return
        print(f"Found {len(images)} image(s), processing begins...")
        for i, img_path in enumerate(tqdm(images)):
            # get all the bone tracings and page with bone tracings replaced by white background, see other file for details of the class
            output = RubbingCropper(
                img_path, text_threshold, mode=mode, padding=padding
            ).output
            for j, bone in enumerate(output["images"]):
                box = output["boxes"][j]
                save_name = f"{os.path.basename(img_path).split('.')[0]}-{[box[0], box[1], box[2], box[3]]}.png"
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                if not os.path.exists(os.path.join(save_path, "images")):
                    os.makedirs(os.path.join(save_path, "images"))
                if not only_object and not os.path.exists(
                    os.path.join(save_path, "pages")
                ):
                    os.makedirs(os.path.join(save_path, "pages"))
                # save the bone tracings
                Image.fromarray(bone).save(
                    os.path.join(save_path, "images", save_name), dpi=(dpi, dpi)
                )
                # save the page with bone tracings replaced by white background
                if not only_object:
                    Image.fromarray(output["page"]).save(
                        os.path.join(
                            save_path,
                            "pages",
                            f"{os.path.basename(img_path).split('.')[0]}.png",
                        ),
                        dpi=(dpi, dpi),
                    )


if __name__ == "__main__":
    # Usage example: python pdfcropper.py --src_pdf="../test/test.pdf" --dst_path="../output" --mode="poly" --dpi=600 --start_page=1 --text_threshold="200, 100" --only_object=True
    parser = argparse.ArgumentParser(
        description="Parse a pdf file and crop out the primary object as images"
    )

    parser.add_argument(
        "--src_path",
        type=str,
        required=True,
        help="path to the pdf file to be parsed, or path to a folder containing images to be parsed",
    )
    parser.add_argument(
        "--dst_path",
        type=str,
        required=True,
        help="path to the output folder, the folder will be created if not exist, and two subfolders will be created, one for the cropped bone tracings, and one for the pages with bone tracings replaced by white background",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="poly",
        required=False,
        help="the mode for cropping the bone tracings, rect will use the bounding rectangle of the contours, poly will use the polygon outline of the contours. Polygon will result in much higher precision cropping, however, it has problems with open contours. Rects is safer in most cases, however, if the one of the tracings is extending into the margin of the other one (overlapped boxes), it will cancel each other out.",
    )
    parser.add_argument(
        "--padding",
        type=str,
        default="white",
        required=False,
        help="can be either white, black or transparent, the padding color for the cropped images, default is white",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        required=False,
        help="resolution of the image to be saved. Abbyy finereader image conversion use a 600dpi, consider changing this if needed to avoid image dimension discrepancy",
    )
    parser.add_argument(
        "--start_page",
        type=int,
        default=1,
        required=False,
        help="the page number to start parsing, if not specified, will start from the first page",
    )
    parser.add_argument(
        "--end_page",
        type=int,
        default=-1,
        required=False,
        help="the page number to end parsing, if not specified, will parse all pages",
    )
    parser.add_argument(
        "--text_threshold",
        type=str,
        default="250, 100",
        required=False,
        help="the threshold for distinguishing the text and the rubbing (or Primary Object), in width and height, those smaller than the threshold will be considered a number text. Example: 200, 100. In my current version of pdf, the width for a 2-digit number is from 15-30 (depending whether there are postfixes like 正，反), the height is 10-20. For four or five digits, width might be 50-100. Also take into account the erosion morphing which will expand the number pixels depending on the kernal size used. So, give it a 50% to 100 percent reserve space.",
    )
    parser.add_argument(
        "--only_object",
        type=lambda x: (
            str(x).lower() == "true"
        ),  # enable argparse to convert string "False" to boolean value
        default=True,
        required=False,
        help="if true, only the bone tracings will be saved, the page with bone tracings replaced by white background will not be saved",
    )

    args = parser.parse_args()
    text_threshold = tuple([int(i.strip()) for i in args.text_threshold.split(",")])
    parse_pdf(
        args.src_path,
        args.dst_path,
        args.mode,
        args.padding,
        args.start_page,
        args.end_page,
        args.dpi,
        text_threshold,
        args.only_object,
    )
