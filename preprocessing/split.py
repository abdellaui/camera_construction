from options import SplitOptions
import os
import numpy as np
from datetime import datetime

opt = SplitOptions().parse()
root = opt.dataroot
datafile = os.path.join(root , "dataset.txt")
valid_size = opt.valid_size
seed = opt.seed
shuffle = opt.shuffle

def storeData(data, dataset):
    with open(os.path.join(root , "dataset_{}.txt".format(dataset)), "w+") as file:
        now = datetime.now()
        header = "{} dataset created on {} \nImageFile, Camera Position [X Y Z W P Q R] \n\n".format(dataset, now)
        file.write(header)
        for item in data:
            stringLine = ' '.join(str(x) for x in item)
            file.write(stringLine)
        file.close()
    
def main():
    error_msg = "[!] valid_size should be in the range [0, 1]."
    assert ((valid_size >= 0) and (valid_size <= 1)), error_msg

    dataArray = np.loadtxt(datafile, dtype=str, delimiter=" ", skiprows=3)
    num_train = len(dataArray)
    indices = list(range(num_train))
    split = int(np.floor(valid_size * num_train))

    if shuffle:
        np.random.seed(seed)
        np.random.shuffle(indices)

    train_indeces = indices[split:]
    valid_indeces = indices[:split]
    train_data = dataArray[train_indeces]
    valid_data = dataArray[valid_indeces]

    
    storeData(train_data, "train")
    storeData(valid_data, "valid")

    print("Total: {} \t test: {} valid: {}".format(num_train, split, num_train-split))
        
    pass


if __name__ == "__main__":
    main()