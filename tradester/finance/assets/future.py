from .asset import Asset



class Future(Asset):
    
    def __init__(self, contract, universe, bar, meta):
        super().__init__('FUT', contract, universe, bar, meta)
