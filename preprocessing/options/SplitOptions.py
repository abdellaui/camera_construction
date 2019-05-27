from .BaseOptions import BaseOptions


class SplitOptions(BaseOptions):
    def initialize(self):
        BaseOptions.initialize(self)
        self.parser.add_argument("--valid_size", type=float, default=0.2, help="percentage split of the training set used for the validation set. Should be a float in the range [0, 1]")
        self.parser.add_argument("--shuffle", type=bool, default=True, help="whether to shuffle the train/validation indices")
        self.parser.add_argument("--seed", type=int, default=0, help="fix seed for reproducibility")
