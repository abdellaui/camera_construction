import argparse
import os

class BaseOptions():
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.initialized = False
        self.opt = None

    def initialize(self):
        self.parser.add_argument("--dataroot", required=True, help="path to images (should have dataset.txt and subfolder img)")



        self.initialized = True

    def parse(self):
        if not self.initialized:
            self.initialize()
        self.opt = self.parser.parse_args()
        return self.opt