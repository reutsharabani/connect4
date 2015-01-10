__author__ = 'reuts'
import logging
import os
import unittest

LOGGER = logging.getLogger("ninarow")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class Piece(object):

    def __init__(self, x, y):
        self.owner = None
        self.location = (x, y,)

    def is_taken(self):
        return self.owner.id != -1

    def __str__(self):
        return "[Piece at %s taken by %s]" % (self.location, self.owner)


class LocationTakenError(Exception):
    pass


class Board(object):

    def __init__(self, number_of_players, rows=6, columns=7, goal=4):
        self._rows = rows
        self._columns = columns
        self._goal = goal

        self._board = [[None for _ in range(columns)] for _ in range(rows)]
        dummy_player = Player(-1)
        for row in range(rows):
            for col in range(columns):
                piece = Piece(row, col)
                self._board[row][col] = piece
                piece.owner = dummy_player

        self._players = []
        for player in range(1, number_of_players+1):
            self._players.append(Player(player))

        LOGGER.debug("%d X %x board initialized: %s" % (rows, columns, str(self._board)))
        # self.__print_board()

    def get_size(self):
        return self._rows, self._columns

    def __win_by_row_from_location(self, row, col, player, left):
        try:
            if left == 0:
                return True
            return self._board[row][col].owner == player and self.__win_by_row_from_location(row+1, col, player, left-1)
        except IndexError:
            return False

    def __win_by_col_from_location(self, row, col, player, left):
        try:
            if left == 0:
                return True
            return self._board[row][col].owner == player and  self.__win_by_col_from_location(row, col+1, player, left-1)
        except IndexError:
            return False

    def __win_from_location(self, row, col, player, left):
        return self.__win_by_col_from_location(
            row, col, player, left
        ) or self.__win_by_row_from_location(
            row, col, player, left
        )

    def __board_won(self):
        for row in range(self._rows):
            for col in range(self._columns):
                player = self._board[row][col].owner
                if player.id == -1:
                    continue
                if self.__win_from_location(row, col, player, self._goal):
                    return player

    def put_one(self, _column, _player):
        if self.__board_won():
            raise BoardWonError("Board already won by player: %s" % self.__board_won())
        for row in reversed(range(self._rows)):
            _piece = self._board[row][_column]

            LOGGER.debug("Trying to put %s in %d, %d - %s" % (_player, row, _column, _piece))
            if not _piece.is_taken():
                _piece._owner = _player
                return _player

        raise LocationTakenError()

    def get_piece(self, x, y):
        return self._board[x][y]

    def __str__(self):
        return os.linesep.join(map(str, [map(lambda x: x.owner.id, self._board[row]) for row in range(self._rows)]))


class Player(object):

    def __init__(self, _id):
        self.id = _id

    def put_one(self, _board, _location):
        return _board.put_one(_location, self)

    def get_color(self):
        return {
            -1: "white",
            1: "blue",
            2: "yellow",
            3: "green",
            4: "red"
        }[self.id]

    def __str__(self):
        return "Player: %d" % self.id


class BoardWonError(Exception):
    pass


class test_ninarow_logic(unittest.TestCase):

    def setUp(self):
        self._board = Board(2)
        self._player1, self._player2 = self._board._players
        print "player 1: %s" % self._player1
        print "player 2: %s" % self._player2

    def test_simple_put(self):
        self._player1.put_one(self._board, 0)
        assert self._board._board[-1][0].owner is self._player1, self._board._board[-1][0].owner

    def test_put_over(self):
        self._player1.put_one(self._board, 0)
        self._player1.put_one(self._board, 0)
        assert self._board._board[-2][0].owner is self._player1, self._board._board[-2][0].owner

    def test_simple_vertical_win(self):
        self._player1.put_one(self._board, 0)
        self._player1.put_one(self._board, 0)
        self._player1.put_one(self._board, 0)
        self._player1.put_one(self._board, 0)
        self.assertRaises(BoardWonError, self._player1.put_one, self._board, 0)

    def test_vertical_win_with_two_players(self):
        self._player1.put_one(self._board, 0)
        self._player2.put_one(self._board, 1)
        self._player1.put_one(self._board, 0)
        self._player2.put_one(self._board, 1)
        self._player1.put_one(self._board, 0)
        self._player2.put_one(self._board, 1)
        self._player1.put_one(self._board, 0)
        self.assertRaises(BoardWonError, self._player2.put_one, self._board, 0)

    def test_simple_horizontal_win(self):
        self._player1.put_one(self._board, 0)
        self._player1.put_one(self._board, 1)
        self._player1.put_one(self._board, 2)
        self._player1.put_one(self._board, 3)
        self.assertRaises(BoardWonError, self._player2.put_one, self._board, 4)

    def test_simple_horizontal_win_2_players(self):
        self._player1.put_one(self._board, 0)
        self._player2.put_one(self._board, 0)
        self._player1.put_one(self._board, 1)
        self._player2.put_one(self._board, 1)
        self._player1.put_one(self._board, 2)
        self._player2.put_one(self._board, 2)
        self._player1.put_one(self._board, 3)
        self.assertRaises(BoardWonError, self._player2.put_one, self._board, 3)

    def test_horizontal_win_edge(self):
        self._player1.put_one(self._board, 6)
        self._player2.put_one(self._board, 6)
        self._player1.put_one(self._board, 5)
        self._player2.put_one(self._board, 5)
        self._player1.put_one(self._board, 4)
        self._player2.put_one(self._board, 4)
        self._player1.put_one(self._board, 3)
        print str(self._board)
        with self.assertRaises(BoardWonError, self._player2.put_one, self._board, 3):
            print "ok"

    def test_vertical_win_edge(self):
        self._player1.put_one(self._board, 1)
        self._player2.put_one(self._board, 1)
        self._player1.put_one(self._board, 1)
        self._player2.put_one(self._board, 2)
        self._player1.put_one(self._board, 1)
        self._player2.put_one(self._board, 3)
        self._player1.put_one(self._board, 1)
        self._player2.put_one(self._board, 4)
        self._player1.put_one(self._board, 1)
        self.assertRaises(BoardWonError, self._player2.put_one, self._board, 3)

if "__main__" == __name__:
    print "Starting"
    board = Board()
    player1 = Player(1)
    player1.put_one(board, 1)
