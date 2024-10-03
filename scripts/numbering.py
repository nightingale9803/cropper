from PIL import Image
from math import *
import pdfplumber
import os, sys
import argparse
from tqdm import tqdm

sys.path.append("..")


def assign_numbers(src_bones, src_pages, ocr_path, start_page=1, x_tolerance=8):
    bone_files = os.listdir(src_bones)
    with pdfplumber.open(ocr_path) as pdf:
        for i, page in enumerate(tqdm(pdf.pages)):
            page_width = page.width
            page_height = page.height
            page_path = os.path.join(src_pages, f"{i+start_page}.png")
            page_dimensions = Image.open(page_path).size
            # normalize the ratio discrepancy caused by DPI difference
            aver_ratio = (
                page_dimensions[0] / page_width + page_dimensions[1] / page_height
            ) / 2
            # extract words, can set a higher x_tolerance to merge adjcant numbers if there is problems
            words = page.extract_words(x_tolerance=x_tolerance)
            # number text, there might be useless text like "典宾"、"宾一" which does not matter
            texts = [word["text"] for word in words]
            center_points = [
                (
                    (word["x0"] + word["x1"]) / 2 * aver_ratio,
                    (word["top"] + word["bottom"]) / 2 * aver_ratio,
                )
                for word in words
            ]
            # get the bounding boxes of the bones from the image dir
            # get the correct bones with the same page number
            correct_page_num = i + start_page
            bone_paths = [
                path
                for path in bone_files
                if int(path.split("-")[0]) == correct_page_num
            ]
            # assign the numbers to the bones by renaming the files
            for bone_path in bone_paths:
                box = eval(
                    bone_path.split("-")[1].replace(".png", "")
                )  # bounding box list [x, y, w, h]
                # get the closest text to it by calculating the distance between the center of the text to the bottom center of the box (as the text is always at the exact bottom or near bottom)
                distances = [
                    sqrt(
                        (center[0] - (box[0] + box[2] / 2)) ** 2
                        + (center[1] - (box[1] + box[3])) ** 2
                    )
                    for center in center_points
                ]
                closest_text = texts[distances.index(min(distances))]
                # rename the bone file with the closest text
                try:
                    os.rename(
                        os.path.join(src_bones, bone_path),
                        os.path.join(
                            src_bones, f"{correct_page_num}-{closest_text}.png"
                        ),
                    )
                except:
                    print(
                        f"Error in renaming {bone_path}, multiple bones are assigned to this number, please check manually afterwards."
                    )
                    # skip rename
                    continue
            page.close()  # release memory


if __name__ == "__main__":
    # Usage example: python numbering.py --src_bones="..\output\bones" --src_pages="..\output\pages" --src_ocr="..\output\ocr.pdf" --x_tolerance=8 --start_page=1
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src_bones",
        type=str,
        required=True,
        help="path to the folder containing bone tracings",
    )
    parser.add_argument(
        "--src_pages",
        type=str,
        required=True,
        help="path to the folder containing page images, needed for calcaulating the correct DPI difference",
    )
    parser.add_argument(
        "--src_ocr",
        type=str,
        required=True,
        help="path to the ocr pdf file containing numbers",
    )
    parser.add_argument(
        "--start_page",
        type=int,
        required=False,
        default=1,
        help="the start page number of the bones in the original pdf, change to the correct one if pages are skipped when parsing the pdf into images. See other script for details",
    )
    parser.add_argument(
        "--x_tolerance",
        type=int,
        default=8,
        help="x tolerance for merging adjacent numbers, set a higher value if some numbers are not merged into a single one",
    )

    args = parser.parse_args()
    assign_numbers(
        args.src_bones, args.src_pages, args.src_ocr, args.start_page, args.x_tolerance
    )
