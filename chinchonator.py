"""
Plays 'Chinchon' (the card game) against a human opponent or itself
Copyright (C) 2019 Pablo Martín <pablo@odkq.com>
This is distributed under the GPL license, see LICENSE file for details
"""

import re
import cmd
import sys
import copy
import random
import itertools


def colorize(inputstr, colornum):
    ''' Use ANSI scape sequences to colorize string '''
    return "\033[1;{};40m{}\033[0;37;40m".format(colornum, inputstr)


def pinfo(inputstr):
    print(colorize(' *** ' + inputstr, 36))


def pdebug(inputstr):
    print(colorize(inputstr, 30))


def perror(inputstr):
    print(colorize('ERROR: ' + inputstr, 31))


class ParseError(Exception):
    pass


class Card:
    """
    The spanish deck has 40 cards,
     with 4 suits ('Bastos', 'Copas', 'Espadas', 'Oros')
     and 10 cards each (from 1 to 7 and 3 'figuras':
      10 (Sota), 11 (Caballo), 12 (Rey)
    Internally Sota, Caballo and Rey will be 8, 9, 10 to
    ease calculations, but shown their traditional numbers
    on representation (__repr__)
    """
    suit_color = {
            "Bastos": 32,
            "Espadas": 34,
            "Copas": 35,
            "Oros": 33}

    def __init__(self, suit, number):
        self.suit = suit
        self.number = number

        # XXX: Check this when playing with a 52 cards deck
        if (self.number > 10):
            self.value = 10
        else:
            self.value = self.number

        if self.number > 12:
            raise ParseError('Number {} too high'.format(self.number))

    def __repr__(self):
        number = self.number
        if number > 7:
            number = self.number + 2
        return colorize('{}{}'.format(number, self.suit[0]),
                        Card.suit_color[self.suit])


class ParsedCard(Card):
    """ Initialize a card object from a string like '10C' """
    def __init__(self, cardstr):
        splitted = re.split('(\d+)', cardstr)
        if len(splitted) != 3:
            raise ParseError('Unable to parse card "{}"'.format(cardstr))
        try:
            number = int(splitted[1])
            if number > 9:
                number = number - 2
        except ValueError:
            raise ParseError('Unable to parse card "{}"'.format(cardstr))
        suit = None
        for key in Card.suit_color.keys():
            if key[0] == splitted[2]:
                suit = key
                break
        if suit is None:
            raise ParseError('Unable to parse card "{}"'.format(cardstr))
        Card.__init__(self, suit, number)


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
        try:
            return self.cards.pop()
        except IndexError:
            # Reshuffle cards from table
            for index in range(len(self.table) - 1):
                self.cards.append(self.table[index])
            for index in range(len(self.table) - 1):
                del self.table[0]
            pinfo('Reshuffling cards from table ...')
            random.shuffle(self.cards)
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
        try:
            return self.table[len(self.table) - 1]
        except IndexError:
            return 'Empty'


class IllegalMovement(Exception):
    pass


class Hand:
    '''
    The player (hand) has 7 cards. He starts its turn by getting a card,
    either face up (from the deck) or up (from the table). After that he
    puts a card on top of the table (deck.put())
    '''
    def __init__(self, deck, name):
        self.deck = deck
        self.name = name
        self.cards = []
        for i in range(7):
            self.cards.append(self.deck.get_down())

    def throw(self, position, flip=False):
        if len(self.cards) != 8:
            raise IllegalMovement("Can't throw before getting")

        if flip:
            toeval = copy.copy(self.cards)
            del toeval[position]
            pos, val = self.evaluate(toeval)
            if val > 4:
                raise IllegalMovement("Can't flip with more than 4")

        card = self.cards[position]
        pinfo('{} throwing card in position {}: {}'.format(self.name,
              position, card))
        del self.cards[position]
        self.deck.put(card)

    def get_deck(self):
        if len(self.cards) != 7:
            raise IllegalMovement("Can't get more than one card")
        card = self.deck.get_down()
        if self.name == 'machine':
            pinfo('{} getting card from deck: (not printed)'.format(self.name))
        else:
            pinfo('{} getting card from deck: {}'.format(self.name, card))
        self.cards.append(card)

    def get_table(self):
        if len(self.cards) != 7:
            raise IllegalMovement("Can't get more than one card")
        card = self.deck.get_table()
        pinfo('{} getting card from table: {}'.format(self.name, card))
        self.cards.append(card)

    def value(self):
        return self.evaluate(self.cards)

    def __repr__(self):
        repstr = '{}: '.format(self.name)
        for card in self.cards:
            repstr += repr(card) + ' '
        return(repstr)

    def evaluate_group(self, cards):
        l = len(cards)
        distance = 0
        for i in range(l - 1):
            distance += cards[i + 1].number - (cards[i] + 1)
        return distance

    def straight_evaluate(self, base):
        l = len(base)
        values = [0] * l
        for i in range(l):
            if base[i].value is None:
                print('Null in {}'.format(base))
            else:
                values[i] = base[i].value
        # for n in range(l):
        n = 0
        while True:
            if n >= l:
                break
            elif n >= 2:
                try:
                    if ((base[n].number == (base[n - 1].number + 1)) and
                            (base[n - 1].number == (base[n - 2].number + 1)) and
                            (base[n].suit == base[n - 1].suit) and
                            (base[n - 1].suit == base[n - 2].suit)):
                        if (values[n - 1] != 0) and (values[n -2] != 0):
                            # Avoid:
                            # > evaluate 3B 10B 4B 10C 10O 11O 12O
                            # Best (10B, 10C, 10O, 11O, 12O, 3B, 4B) Value 7
                            # n += 2
                            values[n] = 0
                            values[n - 1] = 0
                            values[n - 2] = 0
                    elif ((base[n].number == base[n - 1].number) and
                            (base[n - 1].number == base[n - 2].number)):
                        if (values[n - 1] != 0) and (values[n -2] != 0):
                            values[n] = 0
                            values[n - 1] = 0
                            values[n - 2] = 0
                        # n += 2
                    else:
                        values[n] = base[n].value
                except IndexError as e:
                    print("Index n {} l {}".format(n, l))
                    raise e
            else:
                values[n] = base[n].value
            n += 1
        total = 0
        for value in values:
            total += value
        positional = list(reversed(range(l)))
        for n in range(l):
            if values[n] == 0:
                positional[n] = 0
        total_pos = 0
        for value in positional:
            total_pos += value
        return total, total_pos

    def evaluate(self, base=None):
        ''' Calculate all and best value of hand (lower is better) '''
        if base is None:
            base = self.cards
        # Evaluate all possible permutations of the cards
        # For any given combination, like 1O 2O 3O 9E 9O 9B 4E
        # we will get some combination where the remaining card is
        # at the end, so we would store the combination that brings
        # that with the fewer remaining points
        min_value = 900
        min_pos = None
        best_position = None
        for position in itertools.permutations(base):
            current_value, current_pos = self.straight_evaluate(position)
            if current_value < min_value:
                min_value = current_value
                if min_pos is None:
                    min_pos = current_pos
                best_position = position
            elif current_value == min_value:
                if min_pos > current_pos:
                    best_position = position
                    min_pos = current_pos
        return best_position, min_value

        # print('Best position: {} value {}'.format(best_position, min_value))

    def deck_or_table(self):
        ''' Decide wether it is best to get the card from the deck or the
            table '''
        curpos, curval = self.value()
        deck = self.deck.last()
        toeval = copy.copy(self.cards)
        toeval.append(deck)
        pos, val = self.evaluate(toeval)
        if val < curval:
            return False         # Do table
        return True              # Do deck

    def move(self):
        if self.deck_or_table():
            self.get_deck()
        else:
            self.get_table()
        pos, val = self.evaluate()
        to_throw = pos[7]
        nthrow = -1
        for num, card in enumerate(self.cards):
            if to_throw == card:
                nthrow = num
                break
        if nthrow == -1:
            raise Exception("WOT")

        toeval = copy.copy(self.cards)
        del toeval[nthrow]
        pos, val = self.evaluate(toeval)
        if val < 5 and pos[6].number < 5:
            return nthrow
        else:
            self.throw(nthrow)
            return -1


class Game(cmd.Cmd):
    prompt = '> '

    def __init__(self):
        self.human_count = 0
        self.machine_count = 0
        cmd.Cmd.__init__(self)
        self.reset()
        self._update_prompt()

    def reset(self):
        self.deck = Deck()
        pinfo('Shuffling ...')
        pinfo('Giving cards ...')
        self.human = Hand(self.deck, 'human')
        self.machine = Hand(self.deck, 'machine')
        self.deck.first_up()

    def _update_prompt(self):
        print(str(self.human) + ' top card: ' + str(self.deck.last()))

    def postcmd(self, stop, line):
        self._update_prompt()
        return False

    def do_quit(self, args):
        'Quit the game'
        print('Exiting ...')
        sys.exit(0)

    def do_debug(self, args):
        'Show debugging info'
        pdebug('Debugging info: --- ')
        print(self.human)
        pos, val = self.human.value()
        print('Best position {} value {}'.format(pos, val))
        print(self.machine)
        pos, val = self.machine.value()
        print('Best position {} value {}'.format(pos, val))
        print(self.deck)
        pdebug(' ------------------- ')

    def do_throw(self, args):
        'Throw a card, face up to the table'
        try:
            position = int(args) - 1
            if position < 0 or position > 7:
                raise ValueError
            self.human.throw(position)
            flip_pos = self.machine.move()
            if flip_pos != -1:
                self.flip(flip_pos)


        except ValueError:
            perror("Specify a position to throw from 1 to 8")
        except IllegalMovement as e:
            perror(str(e))

    def do_flip(self, args):
        'Throw a card face down (this finish the deal)'
        try:
            position = int(args) - 1
            if position < 0 or position > 7:
                raise ValueError
            self.flip(position, human=True)
        except ValueError:
            perror("Specify a position to flip from 1 to 8")
        except IllegalMovement as e:
            perror(str(e))

    def flip(self, position, human=False):
        if human:
            self.human.throw(position, flip=True)
        else:
            self.machine.throw(position, flip=True)

        hpos, hval = self.human.value()
        mpos, mval = self.machine.value()

        if mval == 0:
            mval = -10
        if hval == 0:
            hval = -10
        print("Machine best position: {} Value {}".format(mpos, mval))
        print("Human best position: {} Value {}".format(hpos, hval))

        self.machine_count += mval
        self.human_count += hval

        print("Total points for human: {}".format(self.human_count))
        print("Total points for machine: {}".format(self.machine_count))

        if (self.human_count > 100):
            print("Machine won")
            self.machine_count = 0
            self.human_count = 0
        if (self.machine_count > 100):
            print("Human won")
            self.machine_count = 0
            self.human_count = 0

        self.reset()

    def do_deck(self, args):
        'Get card from the deck'
        try:
            self.human.get_deck()
        except IllegalMovement as e:
            perror(str(e))

    def do_table(self, args):
        'Get card from the table'
        try:
            self.human.get_table()
        except IllegalMovement as e:
            perror(str(e))

    def do_move(self, args):
        'Perform automatic movement'
        do_loop = False
        if 'loop' in args.split(' '):
            do_loop = True
        while(True):
            flip_pos = self.human.move()
            if flip_pos != -1:
                self.flip(flip_pos, human=True)
                do_loop = False
            flip_pos = self.machine.move()
            if flip_pos != -1:
                self.flip(flip_pos, human=False)
                do_loop = False
            if 'debug' in args.split(' ') and do_loop:
                self.do_debug('')
            if not do_loop:
                break

    def do_evaluate(self, args):
        '''Evaluate current position or a new one.
           Example: evaluate 1O 2O 3O 5E 5O 5B 7E'''
        if args == '':
            # Evaluate current hand
            pos, val = self.human.evaluate()
            print("Best {} Value {}".format(pos, val), end=' ')
            return
        base = []
        straight = False
        for cardstr in args.split(' '):
            if cardstr == 'straight':
                straight = True
                continue
            try:
                card = ParsedCard(cardstr)
            except ParseError as e:
                perror(str(e))
                return
            base.append(card)
        # Evaluate given hand
        if straight:
            pos, val = self.human.straight_evaluate(base)
        else:
            pos, val = self.human.evaluate(base)
        print("Best {} Value {}".format(pos, val), end=' ')

    def default(self, args):
        perror('Unknown syntax: {}'.format(args))


if __name__ == '__main__':
    game = Game()
    game.cmdloop()
