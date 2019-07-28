"""
Plays 'Chinchon' (the card game) against a human opponent or itself
Copyright (C) 2019 Pablo Martín <pablo@odkq.com>
This is distributed under the GPL license, see LICENSE file for details
"""

import random


class Card:
    """
    The spanish deck has 40 cards,
     with 4 suits ('Bastos', 'Copas', 'Espadas', 'Oros')
     and 10 cards each (from 1 to 7 and 3 'figuras':
      10 (Sota), 11 (Caballo), 12 (Rey)
    """
    def __init__(self, suit, number):
        self.suit = suit
        self.number = number
        if (self.number > 10):
            self.value = 10
        else:
            self.value = 7

    def __repr__(self):
        return '{}{}'.format(self.number, self.suit[0])


class Deck:
    """
    A deck is a randomized array of all cards and an empty stack (table)

    Players get either a card face down from the deck or the last thrown
    card in the table (face up)

    After shuffling and giving 7 cards to each player the table is
    initialized by turning up the top card in the row
    """
    def __init__(self):
        self.cards = []
        self.table = []
        for suit in ['Bastos', 'Copas', 'Espadas', 'Oros']:
            for number in range(1, 11):
                self.cards.append(Card(suit, number))
        random.shuffle(self.cards)

    def get_down(self):
        return self.cards.pop()

    def get_table(self):
        return self.table.pop()

    def first_up(self):
        self.table.append(self.cards.pop())

    def put(self, card):
        self.table.append(card)

    def __repr__(self):
        repstr = 'Deck: '
        for card in self.cards:
            repstr += repr(card) + ' '
        repstr += '\nTable: '
        for card in self.table:
            repstr += repr(card) + ' '

        return repstr


class Hand:
    '''
    The player (hand) has 7 cards. He starts its turn by getting a card, either
    face up (from the deck) or up (from the table). After that he puts a card
    on top of the table (deck.put())
    '''
    def __init__(self, deck, name):
        self.deck = deck
        self.name = name
        self.cards = []
        for i in range(7):
            self.cards.append(self.deck.get_down())

    def throw(self, position):
        card = self.cards[position]
        self.deck.put(card)

    def get_down(self):
        self.cards.append(self.deck.get_down())

    def get_up(self):
        self.cards.append(self.deck.get_table())

    def __repr__(self):
        repstr = '{}: '.format(self.name)
        for card in self.cards:
            repstr += repr(card) + ' '
        return(repstr)


if __name__ == "__main__":
    deck = Deck()
    print(deck)
    human = Hand(deck, 'human')
    print(human)
    machine = Hand(deck, 'machine')
    print(machine)
    deck.first_up()
    print(deck)
