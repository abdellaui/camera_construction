from .BaseOptions import BaseOptions

class FilterOptions(BaseOptions):
    def initialize(self):
        BaseOptions.initialize(self)
        self.parser.add_argument("-f", "--img_filter", required=True, type=str, help="aviable options: gradma")
        self.parser.add_argument("--kernel_size", type=int, default=5, help="Kernel size")
