__author__ = 'reuts'
import logging
import Queue
import os
import unittest
from random import choice
from collections import defaultdict
from tree import Tree

LOGGER = logging.getLogger("ninarow")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


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
        self.rows = rows
        self.columns = columns
        self.goal = goal

        self.board = [[None for _ in range(columns)] for _ in range(rows)]

        self.players = []
        for player in range(1, number_of_players+1):
            self.players.append(Player(player))

        self.current_player = choice(self.players)

        LOGGER.debug("%d X %x board initialized: %s" % (rows, columns, str(self.board)))

    def get_size(self):
        return self.rows, self.columns

    def __win_from_location_with_direction(self, row, col, player, left, direction):
        try:

            if left == 0:
                return True

            piece = self.board[row][col]
            if not piece:
                return False
            new_row = row + direction[0]
            new_col = col + direction[1]
            return piece.owner == player and self.__win_from_location_with_direction(
                new_row, new_col, player, left-1, direction
            )

        except IndexError:
            return False

    def __win_by_row_from_location(self, row, col, player, left):
        return self.__win_from_location_with_direction(row, col, player, left, (1, 0))

    def __win_by_col_from_location(self, row, col, player, left):
        return self.__win_from_location_with_direction(row, col, player, left, (0, 1))

    def __win_by_diagonal_left_down_from_location(self, row, col, player, left):
        return self.__win_from_location_with_direction(row, col, player, left, (1, 1))

    def __win_by_diagonal_left_up_from_location(self, row, col, player, left):
        return self.__win_from_location_with_direction(row, col, player, left, (1, -1))

    def __win_from_location(self, row, col, player, left):
        return self.__win_by_col_from_location(
            row, col, player, left
        ) or self.__win_by_row_from_location(
            row, col, player, left
        ) or self.__win_by_diagonal_left_down_from_location(
            row, col, player, left
        ) or self.__win_by_diagonal_left_up_from_location(
            row, col, player, left
        )

    def board_won(self):
        for row in range(self.rows):
            for col in range(self.columns):
                piece = self.board[row][col]
                if not piece:
                    continue
                player = piece.owner
                if player.id == -1:
                    continue
                if self.__win_from_location(row, col, player, self.goal):
                    return player
        return False

    def move_turn_to_next_player(self):
        self.skip_players(1)

    def move_turn_to_previous_player(self):
        self.skip_players(-1)

    def skip_players(self, step):
        next_player_index = (self.players.index(self.current_player) + step) % len(self.players)
        self.current_player = self.players[next_player_index]

    def put_one(self, _column, _player):
        if self.current_player != _player:
            raise NotYourTurnError("This is player %s's turn! Not player %s's." % (self.current_player, _player))
        if self.board_won():
            raise BoardWonError("Board already won by player: %s" % self.board_won())
        for row in reversed(range(self.rows)):
            _piece = self.board[row][_column]

            LOGGER.debug("Trying to put %s in %d, %d - %s" % (_player, row, _column, _piece))
            if not _piece:
                self.board[row][_column] = Piece(row, _column, _player)
                self.move_turn_to_next_player()
                self.moves.append((self.current_player, row, _column,))
                return row, _column

        raise LocationTakenError()

    def undo(self):
        if len(self.moves) > 0:
            player, row, column = self.moves.pop()
            self.board[row][column] = None
            self.move_turn_to_previous_player()
            return row, column
        else:
            raise NoMovesPlayedError("No moves have been played yet!")

    def get_piece(self, x, y):
        return self.board[x][y]

    def get_players(self):
        return self.players

    def __str__(self):
        return os.linesep.join(map(str, [map(lambda x: (x and x.owner.id) or -1, self.board[row]) for row in range(self.rows)]))

    @property
    def valid_moves_iterator(self):
        if self.board_won():
            return
        for i in xrange(len(self.board[0])):
            # check if column has room
            if self.board[0][i] is None:
                yield i

    def copy(self):
        _board = Board(
            len(self.players), rows=self.rows, columns=self.columns, goal=self.goal
        )
        _board.board = [x[:] for x in self.board]
        # these are not sent on initialization
        _board.players = self.players
        _board.current_player = self.current_player
        return _board

    def simulate_move(self, move):
        new_board = self.copy()
        new_board.put_one(move, new_board.current_player)
        return new_board


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

    # def play(self, _board, move):
    #     return board.simulate_move(move)

    def min_max(self, _board, heuristic=None, depth=5):
        tree = Tree({'moves': [], 'board': _board})

        if not heuristic:
            heuristic = self.open_ended_run_heuristic

        def expand(data):
            brd = data['board']
            return [{'move': move, 'board': brd.simulate_move(move)} for move in brd.valid_moves_iterator]

        pos_inf = 999999999
        neg_inf = -999999999

        def __min_max_prunning(node, _depth, alpha=neg_inf, beta=pos_inf, max_turn=True):
            # print "depth: %d" % _depth
            if _depth == 0:
                return heuristic(node.data)
            new_data = expand(node.data)
            if new_data:
                # print "expanding"
                for data in new_data:
                    node.add_child(data)
            else:
                return heuristic(node.data)
            if max_turn:
                best_value = {'score': neg_inf}
                for child in node.children:
                    best_value = max(
                        [best_value, __min_max_prunning(child, _depth-1, alpha, beta, False)],
                        key=lambda x: x['score']
                    )
                    alpha = max(alpha, best_value['score'])
                    if beta <= alpha:
                        # print "prunning occurred a:%d, b:%d" % (alpha, beta)
                        break
                return best_value
            else:
                best_value = {'score': pos_inf}
                for child in node.children:
                    best_value = min(
                        [best_value, __min_max_prunning(child, _depth-1, alpha, beta, True)],
                        key=lambda x: x['score']
                    )
                    beta = min(beta, best_value['score'])
                    if beta <= alpha:
                        break
                return best_value

        val = __min_max_prunning(tree, depth)
        # print val
        return val

    def naive_heuristic(self, state):
        _board = state['board']
        res = dict(state)
        if _board.board_won():
            if _board.board_won() == self:
                res.update({'score': 999999})
                return res
            else:
                res.update({'score': -999999})
                return res
        res.update({'score': 1})
        return res

    def open_ended_run_heuristic(self, state):
        _board = state['board']
        res = dict(state)
        if _board.board_won():
            if _board.board_won() == self:
                res.update({'score': 999999})
                return res
            else:
                res.update({'score': -999999})
                return res

        def score(_row, _col, p, running_score=1, direction=None):
            directions = [
                (0, 1),
                (0, -1),
                (1, 0),
                (1, 1),
                (1, -1),
                (-1, 0),
                (-1, 1),
                (-1, -1),
            ]
            try:
                piece = _board.board[_row][_col]
            except IndexError:
                return 0
            if not piece:
                return running_score
            if not piece.owner is p:
                if piece.owner is None:
                    return running_score
                else:
                    return 0
            if piece.owner is p:
                if not direction:
                    # start all directions
                    return running_score * sum(map(
                        lambda x: running_score * score(_row+x[0], _col+x[1], p, running_score+10, x), directions
                    ))
                else:
                    # use direction set before
                    return running_score * score(_row+direction[0], _col+direction[1], p, running_score+10, direction)
        # we recursively value pieces located with option to continue
        my_score = 0
        his_score = 0
        players = _board.players[:]
        players.remove(self)
        him = players[0]
        for row in range(_board.rows):
            for col in range(_board.columns):
                ms = score(row, col, self)
                hs = score(row, col, him)
                my_score += ms
                his_score += hs
        res['score'] = my_score - his_score
        return res


class BoardWonError(Exception):
    pass


class TestNInARow(unittest.TestCase):

    def setUp(self):
        self._board = Board(2)
        self.starting_player, self.second_player = self._board.players
        if not self.starting_player == self._board.current_player:
            # switch in case we got the turns reversed
            self.second_player = self.starting_player
            self.starting_player = self._board.current_player

        print "starting player : %s" % self.starting_player
        print "second player : %s" % self.second_player

    def test_simple_put(self):
        self.starting_player.put_one(self._board, 0)
        assert self._board.board[-1][0].owner is self.starting_player, self._board.board[-1][0].owner

    def test_put_over(self):
        self.starting_player.put_one(self._board, 0)
        self.second_player.put_one(self._board, 1)
        self.starting_player.put_one(self._board, 0)
        assert self._board.board[-2][0].owner is self.starting_player, self._board.board[-2][0].owner
        assert self._board.board[-1][1].owner is self.second_player, self._board.board[-1][1].owner

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
    board = Board(2, rows=7, columns=7, goal=3)
    print board.current_player.min_max(board)
