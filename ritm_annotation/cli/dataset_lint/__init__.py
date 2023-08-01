from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

from tqdm import tqdm
import cv2
import numpy as np

COMMAND_DESCRIPTION = "Looks for common problems in datasets in mask form that are used for finetuning and generated by the annotator"

logger = logging.getLogger(__name__)


def command(parser):
    parser.add_argument('input', type=Path, help="Folder where the ground truths/masks are stored")
    parser.add_argument('-i', '--images', dest='images', type=Path, help="Folder where the dataset images are stored")
    parser.add_argument('-j', '--jobs', dest='jobs', type=int, default=cpu_count(), help="How many concurrent checks")

    def handle(args):
        assert args.input.is_dir(), "Dataset must be a directory"
        assert args.images is None or args.images.is_dir(), "Invalid image directory"
        if args.images is not None:
            logger.info("Using images with masks!")

        def handle_one(item):
            if not item.is_dir():
                logger.warning(f"'{item}': Dataset noise")
                return
            item_img = None
            if args.images is not None:
                image_file = args.images / item.name
                if not image_file.exists():
                    logger.warning(f"'{image_file}': Image file doesn't exist")
                else:
                    item_img = cv2.imread(str(image_file))
                    if item_img is None:
                        logger.error(f"'{item_img}': Invalid image")
                    else:
                        item_img = cv2.cvtColor(item_img, cv2.COLOR_BGR2RGB)
            for mask in item.iterdir():
                mask_img = cv2.imread(str(mask), 0)
                if mask_img is None:
                    logger.error(f"'{mask}': Invalid mask")
                    continue
                if item_img is not None:
                    (wi, hi, di) = item_img.shape
                    (wm, hm) = mask_img.shape
                    if wi != wm:
                        logger.error(f"'{mask}': First dimension doesn't match for image and mask")
                    if hi != hm:
                        logger.error(f"'{mask}': Second dimension doesn't match for image and mask")

        items = list(args.input.iterdir())
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            ops = tqdm(executor.map(handle_one, items, chunksize=8), total=len(items))
            for item in ops:
                pass
    return handle
