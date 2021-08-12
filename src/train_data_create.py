import os
import numpy as np
from PIL import Image, UnidentifiedImageError
import hickle as hkl

import argparse
import random

# Create image datasets.
# Processes images and saves them in train, val splits.
def process_data(DATA_DIR, OUTPUT_DIR):
    splits = {s: [] for s in ['train', 'val']}

    folders = os.listdir(DATA_DIR)
    if len(folders) < 2:
        print("ERROR: Two or more time-series folders are required in the specified folder.")
        print("Please prepare at least two for tarin and val.")
        exit()

    val_len = int(len(folders) / 10)

    if val_len < 1: val_len = 1

    val_folders = []
    while len(val_folders) < val_len:
        n = random.randint(0, len(folders) - 1)
        if not n in val_folders:
            val_folder = folders.pop(n)
            val_folders.append(val_folder)

    splits['train'] = folders
    splits['val'] = val_folders

    height = 0
    width = 0
    try:
        for split in splits:
            folders_list = []
            for folder in splits[split]:
                im_dir = os.path.join(DATA_DIR, folder)
                files = list(os.walk(im_dir, topdown=False))[-1][-1]
                folders_list += [os.path.join(im_dir, files[0])]
            for i, im_file in enumerate(folders_list):
                im = np.array(Image.open(im_file))
                
                height_tmp = im.shape[0]
                width_tmp = im.shape[1]

                if height < height_tmp: height = height_tmp
                if width < width_tmp: width = width_tmp
    except PermissionError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()
    except IndexError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()
    except UnidentifiedImageError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()
    
    desired_im_sz = padding_shape(height, width)

    try:
        for split in splits:
            im_list = []
            source_list = []  # corresponds to recording that image came from
            for folder in splits[split]:
                im_dir = os.path.join(DATA_DIR, folder)
                files = list(os.walk(im_dir, topdown=False))[-1][-1]
                im_list += [os.path.join(im_dir, f) for f in sorted(files)]
                source_list += [split + '-' + folder] * len(files)

            print( 'Creating ' + split + ' data: ' + str(len(im_list)) + ' images')

            X = np.zeros((len(im_list),) + desired_im_sz + (3,), np.uint8)

            for i, im_file in enumerate(im_list):
                im = np.array(Image.open(im_file))
                X[i, :im.shape[0], :im.shape[1]] = im

            hkl.dump(X, os.path.join(OUTPUT_DIR, 'X_' + split + '.hkl'))
            hkl.dump(source_list, os.path.join(OUTPUT_DIR, 'sources_' + split + '.hkl'))
    except PermissionError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()
    except IndexError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()
    except UnidentifiedImageError:
        print("ERROR: Contains non-image files or inappropriate folders.")
        exit()


def padding_shape(height, width):
    padding_height = padding_size(height)
    padding_width = padding_size(width)
    padding_shape_result = (padding_height, padding_width)

    print('Before Padding：height:', height, ' width:', width)
    print('After Padding ：height:', padding_height, ' width:', padding_width)

    return padding_shape_result


def padding_size(num):
    if num % 8 == 0:
        return num
    padding_num = int(num / 8)
    return (padding_num + 1) * 8


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='TRAIN_DATA_CREATE', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('data_dir', type=str, help='data dir')
    parser.add_argument('output_dir', type=str, help='output dir')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir): os.mkdir(args.output_dir)
    process_data(args.data_dir, args.output_dir)