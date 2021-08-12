'''
Code for downloading and processing KITTI data (Geiger et al. 2013, http://www.cvlibs.net/datasets/kitti/)
'''

import os
import requests
from bs4 import BeautifulSoup
import urllib.request
import numpy as np
from imageio import imread
from scipy.misc import imresize
import hickle as hkl

import argparse


# desired_im_sz = (375, 1242)
categories = ['city', 'residential', 'road']

# Recordings used for validation and testing.
# Were initially chosen randomly such that one of the city recordings was used for validation and one of each category was used for testing.
val_recordings = [('city', '2011_09_26_drive_0005_sync')]
#test_recordings = [('city', '2011_09_26_drive_0104_sync'), ('residential', '2011_09_26_drive_0079_sync'), ('road', '2011_09_26_drive_0070_sync')]
#test_recordings = [('residential', '2011_09_26_drive_0079_sync')]

# Download raw zip files by scraping KITTI website
def download_data(DATA_DIR):
    base_dir = os.path.join(DATA_DIR, 'raw/')
    if not os.path.exists(base_dir): os.mkdir(base_dir)
    for c in categories:
        url = "http://www.cvlibs.net/datasets/kitti/raw_data.php?type=" + c
        r = requests.get(url)
        soup = BeautifulSoup(r.content)
        drive_list = soup.find_all("h3")
        drive_list = [d.text[:d.text.find(' ')] for d in drive_list]
        print( "Downloading set: " + c)
        c_dir = base_dir + c + '/'
        if not os.path.exists(c_dir): os.mkdir(c_dir)
        for i, d in enumerate(drive_list):
            print( str(i+1) + '/' + str(len(drive_list)) + ": " + d)
            url = "https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/" + d + "/" + d + "_sync.zip"
            urllib.request.urlretrieve(url, filename=c_dir + d + "_sync.zip")


# unzip images
def extract_data(DATA_DIR):
    for c in categories:
        c_dir = os.path.join(DATA_DIR, 'raw/', c + '/')
        zip_files = list(os.walk(c_dir, topdown=False))[-1][-1]#.next()
        for f in zip_files:
            #print( 'unpacking: ' + f)
            spec_folder = f[:10] + '/' + f[:-4] + '/image_03/data*'
            command = 'unzip -qq ' + c_dir + f + ' ' + spec_folder + ' -d ' + c_dir + f[:-4]
            os.system(command)


# Create image datasets.
# Processes images and saves them in train, val, test splits.
def process_data(DATA_DIR):
    splits = {s: [] for s in ['train', 'val']}
    splits['val'] = val_recordings
    # splits['test'] = test_recordings
    not_train = splits['val']
    for c in categories:  # Randomly assign recordings to training and testing. Cross-validation done across entire recordings.
        c_dir = os.path.join(DATA_DIR, 'raw', c + '/')
        folders= list(os.walk(c_dir, topdown=False))[-1][-2]
        splits['train'] += [(c, f) for f in folders if (c, f) not in not_train]

    for split in splits:
        folders_list = []
        im_list = []
        source_list = []  # corresponds to recording that image came from
        for category, folder in splits[split]:
            im_dir = os.path.join(DATA_DIR, 'raw/', category, folder, folder[:10], folder, 'image_03/data/')
            files = list(os.walk(im_dir, topdown=False))[-1][-1]
            im_list += [im_dir + f for f in sorted(files)]
            source_list += [category + '-' + folder] * len(files)
            folders_list += [os.path.join(im_dir, files[0])]

        print( 'Creating ' + split + ' data: ' + str(len(im_list)) + ' images')

        height = 0
        width = 0
        for i, im_file in enumerate(folders_list):
            im = imread(im_file)
            height_tmp = im.shape[0]
            width_tmp = im.shape[1]

            if height < height_tmp: height = height_tmp
            if width < width_tmp: width = width_tmp
        desired_im_sz = padding_shape(height,width)

        X = np.zeros((len(im_list),) + desired_im_sz + (3,), np.uint8)

        for i, im_file in enumerate(im_list):
            im = imread(im_file)
            X[i, :im.shape[0], :im.shape[1]] = im

        hkl.dump(X, os.path.join(DATA_DIR, 'X_' + split + '.hkl'))
        hkl.dump(source_list, os.path.join(DATA_DIR, 'sources_' + split + '.hkl'))


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


# resize and crop image
def process_im(im, desired_sz):
    target_ds = float(desired_sz[0])/im.shape[0]
    im = imresize(im, (desired_sz[0], int(np.round(target_ds * im.shape[1]))))
    d = int((im.shape[1] - desired_sz[1]) / 2)
    im = im[:, d:d+desired_sz[1]]
    return im


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('data_dir', type=str, help='data dir')
    parser.add_argument('-d', '--download', action='store_true')
    parser.add_argument('-p', '--process_data', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.data_dir): os.mkdir(args.data_dir)

    if args.download:
        print('downloading images')
        download_data(args.data_dir)
        print('unzip images')
        extract_data(args.data_dir)
    
    if args.process_data:
        print('data processing')
        process_data(args.data_dir)
    
    if not args.download and not args.process_data:
        print("If you want to download kitti data, flag it as -d or --download.")
        print("If you want to compress data to hkl, flag it as -p or --process_data.")