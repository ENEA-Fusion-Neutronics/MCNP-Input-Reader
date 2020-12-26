from .exceptions import CellNotFound

class Store:
    _store = {}
    _store_lines = {}
    
    def __init__(self):
        pass

    def __getitem__(self, id_card: int):
        if id_card in self._store.keys():
            return self._store[id_card]
        else:
            raise CellNotFound('Vaffanculo, {} does not exist!'.format(id_card))
    
    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return (card for card in self._store.values())


