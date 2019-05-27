from .BaseOptions import BaseOptions

class FilterOptions(BaseOptions):
    def initialize(self):
        BaseOptions.initialize(self)
        self.parser.add_argument("--img_filter", required=True, type=str, help="gradma, edge")
        self.parser.add_argument("--kernel_size", type=int, default=5, help="Kernel size")
