# PDF Rubbing Cropper - README

![pdfcropper](example.png)

## 🚀 Get Started

Video Demonstration:
[Download and watch the video](./installation.mp4)

To use the app locally, follow the steps below:

1. Download and extract the code via one of two options:
   - Download the code from this repository (using .zip download above) and extract the files onto a folder on your local machine.
   - Install via `git clone` method (recommended for easy updating):
     - Install [git](https://git-scm.com/downloads) here
     - Open terminal in the directory where you want to install the code (anywhere on your machine)
     - Run the following command in the terminal to clone the repository: `git clone https://github.com/nightingale9803/cropper.git`
2. Install latest [python](https://www.python.org/downloads/) (recommended to follow the default instructions, be sure to check the option to `add python to PATH` during installation)
3. Install latest [pip](https://pip.pypa.io/en/stable/installation/) package manager (should be installed by default with python), if not, manual installation can be done by following actions:
   - Open a terminal from anywhere
   - Run `py -m ensurepip --upgrade` in terminal to install pip (windows)
   - If above does not work, can also refer to this [guide](https://www.geeksforgeeks.org/how-to-install-pip-on-windows/)
4. Install Dependencies

   - Navigate to the project directory (where the code is extracted)
   - Right-Click anywhere inside the folder to open context menu, select `Open In Terminal`
   - Run the following command in the terminal to install all the required packages

```bash
pip install -r requirements.txt
```

📦 Running the Image Cropping Script

- Navigate to the `scripts/` directory
- Open terminal in the `scripts` directory
- Run the following command in the terminal to crop from any PDF file, image, or a folder of images. A minimum example is:

```bash
python pdfcropper.py --src_path="../test/test.pdf" --dst_path="../output"
```
or you can specify more complete parameters like below (parameters can be adjusted as needed):

```bash
python pdfcropper.py --src_path="../test/test.pdf" --dst_path="../output" --mode="poly" --padding="white" --dpi=600 --start_page=1 --end_page=-1 --text_threshold="200, 100" --only_object=True
```

## 📝 Parameters

- `--src-path` : Path to a input PDF file, an image, or a folder containing images. The path can be a relative path like `../data/input.pdf` (relative to current directory) or an absolute path like `C:/Users/username/Documents/input.pdf`, `C:/Users/username/Documents/images`
- `--dst_path`: Path to the output directory where the cropped images will be saved, could be a relative path like `../data/output` or an absolute path like `C:/Users/username/Documents/output`
- `--start_page`: Page number to start cropping from (optional). Default is 1, which is to crop from first page. Omitted when input is image or folder.
- `--end_page`: Page number to end cropping at (optional). Default is -1, which means crop till the last page. Omitted when input is image or folder.
- `--mode`: Mode of cropping (optional). Can be `rect` or `poly`. `rect` mode will use the bounding rectangle of the contours (x, y, width, height), `poly` will use the polygon outline of the contours ((x0, y0), (x1, y1), ...). Polygon will result in much higher precision cropping, on account of it wraps around the object tightly using polygon approximation, however, it has problems with open contours. Rectangles are safer in most cases, however, if the one of the primary objects is extending into the margin of the other one (overlapped boxes), it will cancel each other out, which could happen a lot in modern publications. In most cases, "poly" mode is recommended, unless the objects-to-be-cropped have unclosed shapes.
- `--padding`: The color of the padding around the cropped image (optional). Could be `white`, `black`, or `transparent`. Normally, white is recommend as most modern publications use white background pages, and the padding will be less noticeable. However, some tasks require transparent-background images, so `transparent` option is offered here. But note that as this project is based on traditional algorithms, the outline detection underwent erosion (edge expansion), which will cause the cropping not exactly wrapping around the objects.
- `--dpi`: Resolution of the image to be saved (optional). Usually higher value results in larger and clearer images. But different PDF engines has different built-in resolution, often the native value of the source PDF might be preferred to maintain consistency. For instance, Abbyy finereader image conversion use a 600dpi, consider changing this if needed to avoid image dimension discrepancy. Omited when input is image or folder.
- `--text_threshold`: The threshold for distinguishing between the texts, noises, and the rubbing (or Primary Object) (optional). The two numbers are for width and height in pixels, those smaller than the threshold will be considered a text or irrelevant objects. Example: 200, 100 - ,meaning objects smaller than 200px wide and 100px tall will not be cropped and saved. Threshold should depend on the general pixel size of each page of the PDF, but usually 200,100 should work for most scenerios. The reason for that is, for most moderate quality scanned PDFs, the width for a 2-digit number is about 15-30px (depending whether there are postfixes like 正，反), the height is 10-20 px. For four or five digits, width might be 50-100 px. Also take into account the erosion morphing which will expand the number pixels depending on the kernal size used. So, give it a 50% to 100 percent reserve space, rounding it up to (200px, 100px) for width and height seperately.
- `--only_object`: A parameter for debugging purposes (optional). If true, only the primary objects will be saved, the page with objects replaced by white background will not be saved. This is useful for debugging the precision of the object detection and cropping process and adjustments of relevant parameters.

## ♻️ Updating

To update the code to the latest release, follow one of the two options below:
1. Same as the installation process, download the latest code from the repository and extract the files onto a folder on your local machine.
2. Update via `git` version control system:
   - Install [git](https://git-scm.com/downloads) here (if not already installed)
   - Open terminal in the project directory (where the code is located)
   - Run the command `git pull` to update the code to the latest version

## 🛠️ Debugging

One of the common issues when running the script is `python not recognized as an internal or external command`. Or `pip not recognized as an internal or external command`. This is usually due to the `PATH` variable not being set correctly (usually managed via default python installation). But if such issues occur, you can refer to tutorial like [this](https://realpython.com/add-python-to-path/) to add python to the `PATH` variable.

## 🌲 Project Structure

- `modules/`: Contains the source code for utilities functions and classes that are used in the main script.
- `notebooks/`: Contains the Jupyter Notebooks used for testing and development.
- `scripts/`: Contains the main script for cropping the images from the PDF.
- `test/`: Contains the test PDF files used for testing the script.
- `requirements.txt`: Contains the list of dependencies required for the project.
- `README.md`: Contains the instructions for running the script and other details about the project.
