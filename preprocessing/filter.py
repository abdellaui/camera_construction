from options import FilterOptions
import os
import numpy as np
from datetime import datetime
import cv2
import shutil

opt = FilterOptions().parse()
root = opt.dataroot
dataset = opt.dataset
datafile = os.path.join(root, dataset)
img_filter = opt.img_filter
kernel_size= opt.kernel_size
pathToStore = os.path.join(root , img_filter+ "_" +datetime.datetime.now().strftime('%y-%m-%d_%H-%M-%S'))

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def gragma(img):
    sobelX = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=kernel_size)
    sobelY = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=kernel_size)
    magnitude = np.sqrt(sobelX**2.0 + sobelY**2.0)
    return magnitude

def process(img):
    path = os.path.join(root, img)
    imgPath = os.path.join(pathToStore, img)
    img = cv2.imread(path)
    if img.size == 0:
        return print("{} not found".format(path))
        
    if img_filter == "gradma": 
        img = gragma(img)
    elif img_filter == "otherwise":
        pass
        
    stored = cv2.imwrite(imgPath, img)
    print(stored, imgPath)
    
def main():
    if img_filter in ["gradma"]:
        
        dataArray = np.loadtxt(datafile, dtype=str, delimiter=" ", skiprows=3, usecols = (0))

        mkdir(pathToStore)
        countData = len(dataArray)
        if countData > 0:
            for subdir in dataArray[0].split("/")[0:-1]:
                mkdir(os.path.join(pathToStore , subdir))
            shutil.copy(datafile, os.path.join(pathToStore , dataset))
            
            for i, img in enumerate(dataArray):
                i += 1
                print("{}% \t\t {}/{}".format(round(i/countData*100,2), i, countData))
                process(img)
            print("FINISHED")

if __name__ == "__main__":
    main()