
from .asset import Asset

class Security():

    def __init__(self, ticker, universe, bar, meta):
        super().__init__('SEC', ticker, universe, bar, meta) 

