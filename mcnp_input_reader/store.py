from .exceptions import CardNotFound, CardIdAlreadyUsed
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Card:
    __slots__ = ['card_id', 'start_line', 'end_line']

    card_id: int 
    start_line: int
    end_line: int

    def __post_init__(self):
        pass

class Store:
    _store: Dict[int, Card] 
    
    def __init__(self, card_list = []):
        self._store = {}
        self.cardnotfound_exception = CardNotFound
        self.cardidalreadyused_exception = CardIdAlreadyUsed
        self.card_name = 'card'
        for card in card_list:
            self.add(card)
    
    def __getitem__(self, card_id: int):
        if card_id in self._store.keys():
            return self._store[card_id]
        else:
            raise self.cardnotfound_exception('Vaffanculo, {} {} does not exist!'.format(self.card_name, card.id))

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return (card for card in self._store.values())

    def __repr__(self):
        class_name = self.__class__.__name__
        ids = ', '.join([str(card.id) for card in self._store.values()])
        return '<{}>: [{}]'.format(class_name, ids)

    def add(self, card):
        if self._store.get(card.id, False):
           raise self.cardidalreadyused_exception('Vaffanculo, the {} {} has been already used'.format(self.card_name, card.id))
        else:
            self._store[card.id] = card
   
    def filter(self, p):
        return self.__class__(list(filter(p, self.__iter__())))
        #for card in list(filter(p, self.__iter__())):
        #    filtered.add(card)
        #return filtered

