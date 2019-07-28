"""
Plays 'Chinchon' (the card game) against a human opponent or itself
Copyright (C) 2019 Pablo Martín <pablo@odkq.com>
This is distributed under the GPL license, see LICENSE file for details
"""

import cmd
import random
import sys


def colorize(inputstr, colornum):
    ''' Use ANSI scape sequences to colorize string '''
    return "\033[1;{};40m{}\033[0;37;40m".format(colornum, inputstr)

def pinfo(inputstr):
    print(colorize(' *** ' + inputstr, 36))

def pdebug(inputstr):
    print(colorize(inputstr, 30))

def perror(inputstr):
    print(colorize('ERROR: ' + inputstr, 31))


class Card:
    """
    The spanish deck has 40 cards,
     with 4 suits ('Bastos', 'Copas', 'Espadas', 'Oros')
     and 10 cards each (from 1 to 7 and 3 'figuras':
      10 (Sota), 11 (Caballo), 12 (Rey)
    """
    suit_color = {
            "Bastos": 32,
            "Espadas": 34,
            "Copas": 35,
            "Oros": 33 }

    def __init__(self, suit, number):
        self.suit = suit
        self.number = number
        if (self.number > 10):
            self.value = 10
        else:
            self.value = self.number

    def __repr__(self):
        return colorize('{}{}'.format(self.number, self.suit[0]),
                        Card.suit_color[self.suit])


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

    def last(self):
        return self.table[len(self.table) - 1]


class IllegalMovement(Exception):
    pass


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
        if len(self.cards) != 8:
            raise IllegalMovement("Can't throw before getting")

        card = self.cards[position]
        pinfo('*** {} Putting card in position {}: {}'.format(self.name,
              position, card))
        del self.cards[position]
        self.deck.put(card)

    def get_deck(self):
        if len(self.cards) != 7:
            raise IllegalMovement("Can't get more than one card")
        card = self.deck.get_down()
        pinfo('*** {} Getting card from deck: {}'.format(self.name, card))
        self.cards.append(card)

    def get_table(self):
        if len(self.cards) != 7:
            raise IllegalMovement("Can't get more than one card")
        card = self.deck.get_table()
        pinfo('*** {} Getting card from table: {}'.format(self.name, card))
        self.cards.append(card)

    def value(self):
        val = 0
        for card in self.cards:
            val += card.value
        return val

    def __repr__(self):
        repstr = '{}: '.format(self.name)
        for card in self.cards:
            repstr += repr(card) + ' '
        return(repstr)

class Game(cmd.Cmd):
    prompt = '> '

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.deck = Deck()
        pinfo('Shuffling ...')
        pinfo('Giving cards ...')
        self.human = Hand(self.deck, 'human')
        self.machine = Hand(self.deck, 'machine')
        self.deck.first_up()
        self._update_prompt()

    def _update_prompt(self):
        print(str(self.human) + ' top card: ' + str(self.deck.last()))

    def postcmd(self, stop, line):
        self._update_prompt()
        return False

    def do_quit(self, args):
        print('Exiting ...')
        sys.exit(0)

    def do_debug(self, args):
        pdebug('Debugging info: --- ')
        print(self.human)
        print('Value ' + str(self.human.value()))
        print(self.machine)
        print('Value ' + str(self.machine.value()))
        print(self.deck)
        pdebug(' ------------------- ')

    def do_throw(self, args):
        try:
            position = int(args) - 1
            if position < 0 or position > 7:
                raise ValueError
            self.human.throw(position)
        except ValueError:
            perror("Specify a position to throw from 1 to 8")
        except IllegalMovement as e:
            perror(str(e))

    def do_deck(self, args):
        try:
            self.human.get_deck()
        except IllegalMovement as e:
            perror(str(e))

    def do_table(self, args):
        try:
            self.human.get_table()
        except IllegalMovement as e:
            perror(str(e))

    def default(self, args):
        perror('Unknown syntax: {}'.format(args))


if __name__ == '__main__':
    game = Game()
    game.cmdloop()
