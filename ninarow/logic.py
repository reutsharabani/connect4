__author__ = 'reuts'
import logging
import os
import unittest
from random import choice

LOGGER = logging.getLogger("ninarow")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class Piece(object):

    def __init__(self, x, y, owner):
        self.owner = owner
        self.location = (x, y,)

    def __str__(self):
        return "[Piece at %s taken by %s]" % (self.location, self.owner)


class LocationTakenError(Exception):
    pass


class NotYourTurnError(Exception):
    pass


class NoMovesPlayedError(Exception):
    pass


class Board(object):

    def __init__(self, number_of_players, rows=6, columns=7, goal=4):
        self.moves = list()
        self._rows = rows
        self._columns = columns
        self._goal = goal

        self._board = [[None for _ in range(columns)] for _ in range(rows)]

        self._players = []
        for player in range(1, number_of_players+1):
            self._players.append(Player(player))

        self.current_player = choice(self._players)

        LOGGER.debug("%d X %x board initialized: %s" % (rows, columns, str(self._board)))

    def get_size(self):
        return self._rows, self._columns

    def __win_by_row_from_location(self, row, col, player, left):
        try:

            if left == 0:
                return True

            piece = self._board[row][col]
            if not piece:
                return False

            return piece.owner == player and self.__win_by_row_from_location(row+1, col, player, left-1)

        except IndexError:
            return False

    def __win_by_col_from_location(self, row, col, player, left):
        try:

            if left == 0:
                return True

            piece = self._board[row][col]

            if not piece:
                return False

            return piece.owner == player and self.__win_by_col_from_location(row, col+1, player, left-1)

        except IndexError:
            return False

    def __win_from_location(self, row, col, player, left):
        return self.__win_by_col_from_location(
            row, col, player, left
        ) or self.__win_by_row_from_location(
            row, col, player, left
        )

    def board_won(self):
        for row in range(self._rows):
            for col in range(self._columns):
                piece = self._board[row][col]
                if not piece:
                    continue
                player = piece.owner
                if player.id == -1:
                    continue
                if self.__win_from_location(row, col, player, self._goal):
                    return player

    def move_turn_to_next_player(self):
        self.skip_players(1)

    def move_turn_to_previous_player(self):
        self.skip_players(-1)

    def skip_players(self, step):
        next_player_index = (self._players.index(self.current_player) + step) % len(self._players)
        self.current_player = self._players[next_player_index]

    def put_one(self, _column, _player):
        if self.current_player != _player:
            raise NotYourTurnError("This is player %s's turn! Not player %s's." % (self.current_player, _player))
        if self.board_won():
            raise BoardWonError("Board already won by player: %s" % self.board_won())
        for row in reversed(range(self._rows)):
            _piece = self._board[row][_column]

            LOGGER.debug("Trying to put %s in %d, %d - %s" % (_player, row, _column, _piece))
            if not _piece:
                self._board[row][_column] = Piece(row, _column, _player)
                self.move_turn_to_next_player()
                self.moves.append((self.current_player, row, _column,))
                return row, _column

        raise LocationTakenError()

    def undo(self):
        if len(self.moves) > 0:
            player, row, column = self.moves.pop()
            self._board[row][column] = None
            self.move_turn_to_previous_player()
            return row, column
        else:
            raise NoMovesPlayedError("No moves have been played yet!")

    def get_piece(self, x, y):
        return self._board[x][y]

    def get_players(self):
        return self._players

    def __str__(self):
        return os.linesep.join(map(str, [map(lambda x: (x and x.owner.id) or -1, self._board[row]) for row in range(self._rows)]))


class Player(object):

    def __init__(self, _id):
        self.id = _id

    def put_one(self, _board, _location):
        LOGGER.debug("Player %s trying to put a piece in %s" % (self, _location))
        return _board.put_one(_location, self)

    def get_color(self):
        return {
            -1: "white",
            1: "blue",
            2: "yellow",
            3: "green",
            4: "red",
            5: "purple",
            6: "orange"
        }[self.id]

    def __str__(self):
        return "Player: %d" % self.id


class BoardWonError(Exception):
    pass


class TestNInARow(unittest.TestCase):

    def setUp(self):
        self._board = Board(2)
        self.starting_player, self.second_player = self._board._players
        if not self.starting_player == self._board.current_player:
            # switch in case we got the turns reversed
            self.second_player = self.starting_player
            self.starting_player = self._board.current_player

        print "starting player : %s" % self.starting_player
        print "second player : %s" % self.second_player

    def test_simple_put(self):
        self.starting_player.put_one(self._board, 0)
        assert self._board._board[-1][0].owner is self.starting_player, self._board._board[-1][0].owner

    def test_put_over(self):
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 0)
        assert self._board._board[-2][0].owner is self.starting_player, self._board._board[-2][0].owner
        assert self._board._board[-1][1].owner is self.second_player, self._board._board[-1][1].owner

    def test_vertical_win_with_two_players(self):
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 0)
        self.assertRaises(BoardWonError, self.second_player.put_one, self._board, 0)

    def test_double_play_simple(self):
        self.starting_player.put_one(self._board, 0)
        self.assertRaises(NotYourTurnError, self.starting_player.put_one, self._board, 0)

    def test_simple_horizontal_win_2_players(self):
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 0)
        self.starting_player.put_one(self._board, 1)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 2)
        self.second_player.put_one(self._board, 2)
        self.starting_player.put_one(self._board, 3)
        self.assertRaises(BoardWonError, self.second_player.put_one, self._board, 3)

    def test_horizontal_win_edge(self):
        self.starting_player.put_one(self._board, 6)
        self.second_player.put_one(self._board, 6)
        self.starting_player.put_one(self._board, 5)
        self.second_player.put_one(self._board, 5)
        self.starting_player.put_one(self._board, 4)
        self.second_player.put_one(self._board, 4)
        self.starting_player.put_one(self._board, 3)
        print str(self._board)
        self.assertRaises(BoardWonError, self.second_player.put_one, self._board, 3)

    def test_vertical_win_edge(self):
        self.starting_player.put_one(self._board, 1)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 1)
        self.second_player.put_one(self._board, 2)
        self.starting_player.put_one(self._board, 1)
        self.second_player.put_one(self._board, 3)
        self.starting_player.put_one(self._board, 1)
        self.second_player.put_one(self._board, 4)
        self.starting_player.put_one(self._board, 1)
        self.assertRaises(BoardWonError, self.second_player.put_one, self._board, 3)

if "__main__" == __name__:
    print "Starting"
    board = Board(2)
    player1 = Player(1)
    player1.put_one(board, 1)
