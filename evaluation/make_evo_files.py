import argparse
import numpy as np
import time


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s","--dataset", required=True, help="path to dataset.txt")
parser.add_argument("-p","--prefix", type=str, default="", help="prefix for the stored filename")
parser.add_argument("-t","--timestamp", type=int, default=int(time.time()), help="timestamp")
opt = parser.parse_args()



dataArray = np.loadtxt(opt.dataset, dtype=str, delimiter=" ", skiprows=3, usecols = (1,2,3,4,5,6,7))
print("timstamp:", opt.timestamp)
with open(opt.prefix+"evo_dataset.txt", "w+") as file:
    for i, data in enumerate(dataArray):
        newString = "{} {} {} {} {} {} {} {}\n".format(opt.timestamp+i, data[0], data[1], data[2], data[3], data[4], data[5], data[6])
        file.write(newString)
        
    file.close()