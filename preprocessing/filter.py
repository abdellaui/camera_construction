from options import FilterOptions
import os
import numpy as np
from datetime import datetime
import cv2

opt = FilterOptions().parse()
root = opt.dataroot
datafile = os.path.join(root , "dataset.txt")
img_filter = opt.img_filter
kernel_size= opt.kernel_size

def gragma(img):
    sobelX = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=kernel_size)
    sobelY = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=kernel_size)
    magnitude = np.sqrt(sobelX**2.0 + sobelY**2.0)
    return magnitude

def edge(img):
    return img

def process(img):
    path = os.path.join(root, img)
    pathToStore = os.path.join(root , img_filter, img)
    img = cv2.imread(path)
    if not img:
        return print("{} not found".format(path))
        
    if img_filter == "gradma": 
        img = gragma(img)
    elif img_filter == "edge":
        img = edge(img)
        
    cv2.imwrite(pathToStore, img)
    
def main():
    if img_filter in ["gradma", "edge"]:
        dataArray = np.loadtxt(datafile, dtype=str, delimiter=" ", skiprows=3, usecols = (0))
        countData = len(dataArray)
        for i, img in enumerate(dataArray):
            i += 1
            print("{}% \t\t {}/{}".format(round(i/countData*100,2), i, countData))
            process(img)
        print("FINISHED")

if __name__ == "__main__":
    main()