__author__ = 'reuts'
import unittest
from ninarow.utils.tree import Tree
from random import choice
import os
import logging

LOGGER = logging.getLogger("ninarow")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class Game(object):

    def __init__(self, players, rows, columns, goal):

        self.board = Board(players, rows, columns, goal)
        self.goal = goal

    # def start(self):
    #
    #     while True:
    #         if not self.board.get_winner():
    #             # play next player's turn
    #             self.board.put_one(self.board.current_player.get_move(self.board))
    #
    #     raise NotImplementedError("start not implemented yet")


class LocationTakenError(Exception):
    pass


class NotYourTurnError(Exception):
    pass


class NoMovesPlayedError(Exception):
    pass


class BoardWonError(Exception):
    pass


class Board(object):

    def __init__(self, players, rows=6, columns=7, goal=24):
        self.moves = list()
        self.rows = rows
        self.columns = columns
        self.goal = goal

        self.tip_strategy = lambda player: MinMaxStrategy(NaiveHeuristic(player)).get_move(self, 4)
        self.board = [[None for _ in range(columns)] for _ in range(rows)]

        self.players = players

        self.current_player = choice(self.players)

        LOGGER.debug("%d X %x board initialized: %s" % (rows, columns, str(self.board)))

    def is_full(self):
        for row in range(self.rows):
            for col in range(self.columns):
                if self.board[row][col] is None:
                    return False
        return True

    def get_size(self):
        return self.rows, self.columns

    def __win_from_location_with_direction(self, row, col, player, left, direction):

        if left == 0:
            return True

        if not 0 <= row < self.rows:
            return False

        if not 0 <= col < self.columns:
            return False

        piece = self.board[row][col]
        if not piece:
            return False
        new_row = row + direction[0]
        new_col = col + direction[1]
        return piece.owner == player and self.__win_from_location_with_direction(
            new_row, new_col, player, left-1, direction
        )

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

    def get_winner(self):
        for row in range(self.rows):
            for col in range(self.columns):
                piece = self.board[row][col]
                if not piece:
                    continue
                player = piece.owner
                if player.id == -1:
                    continue
                if self.__win_from_location(row, col, player, self.goal):
                    LOGGER.debug("Winner is: " + player.name)
                    return player
        return False

    def move_turn_to_next_player(self):
        self.skip_players(1)

    def move_turn_to_previous_player(self):
        self.skip_players(-1)

    def skip_players(self, step):
        next_player_index = (self.players.index(self.current_player) + step) % len(self.players)
        self.current_player = self.players[next_player_index]

    def put_one(self, _column):
        LOGGER.debug("putting in column: %s" % str(_column))
        _player = self.current_player
        if self.get_winner():
            raise BoardWonError("Board already won by player: %s" % self.get_winner())
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
        return os.linesep.join(
            map(str, [map(lambda x: (x and "%d" % x.owner.id) or 'x', self.board[row]) for row in range(self.rows)])
        )

    @property
    def valid_moves_iterator(self):
        if self.get_winner():
            return
        for i in xrange(len(self.board[0])):
            # check if column has room
            if self.board[0][i] is None:
                yield i

    def copy(self):
        _board = Board(
            self.players, rows=self.rows, columns=self.columns, goal=self.goal
        )
        _board.board = [x[:] for x in self.board]
        # these are not sent on initialization
        _board.current_player = self.current_player
        return _board

    def simulate_move(self, move):
        new_board = self.copy()
        new_board.put_one(move)
        return new_board




POS_INF = 9999999999
NEG_INF = -9999999999


class TooManyPlayersError(Exception):
    pass


class AbstractPlayer(object):

    _ids = 1

    def __init__(self, name):
        if AbstractPlayer._ids > 6:
            raise TooManyPlayersError()
        self.name = name
        self.id = AbstractPlayer._ids
        AbstractPlayer._ids += 1
        LOGGER.debug("added player %s with id %d" % (self.name, self.id))

    def get_move(self, board, column):
        raise NotImplementedError("Move not implemented for abstract player")

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


class HumanPlayer(AbstractPlayer):
    def get_move(self, board, column):
        return column


class BoardFullError(Exception):
    pass


class ComputerMinMaxPlayer(AbstractPlayer):

    _ids = 0

    def __init__(self, heuristic_class, difficulty):
        super(ComputerMinMaxPlayer, self).__init__("pc-min-max-%d" % ComputerMinMaxPlayer._ids)
        self.strategy = MinMaxStrategy(heuristic_class(self))
        self.difficulty = difficulty

    def get_move(self, board, column):
        winner = board.get_winner()
        if winner:
            raise BoardWonError("Board already won by %s" % winner)
        if board.is_full():
            raise BoardFullError("Board full. Undo or quit.")
        return self.strategy.get_move(board, depth=self.difficulty)['moves'][0]


class BaseHeuristic(object):
    def __init__(self, player):
        self.player = player

    def score(self, board):
        raise NotImplemented("Not implemented for base heuristic")


class BaseStrategy(object):
    def __init__(self, heuristic):
        self.heuristic = heuristic
        LOGGER.debug("Created strategy")

    def get_move(self, board):
        raise NotImplemented("Not implemented for base class")


class MinMaxStrategy(BaseStrategy):

    def __init__(self, heuristic):
        LOGGER.debug("Creating minmax strategy")
        super(MinMaxStrategy, self).__init__(heuristic)

    def get_move(self, _board, depth=4):
        LOGGER.info("depth: %d" % depth)
        tree = Tree({'moves': [], 'board': _board})

        LOGGER.debug("moves: %s" % str(list(_board.valid_moves_iterator)))

        def expand(data):
            brd = data['board']
            return [
                {
                    'moves': data['moves'] + [move],
                    'board': brd.simulate_move(move)
                } for move in brd.valid_moves_iterator
            ]

        pos_inf = POS_INF
        neg_inf = NEG_INF

        def __min_max_prunning(node, _depth, alpha=NEG_INF, beta=POS_INF, max_turn=True):
            LOGGER.debug("evaluating node:")
            LOGGER.debug("%s" % str(node.data['board']))
            LOGGER.debug("turn: %s" % node.data['board'].current_player)
            result = dict(node.data)
            if _depth == 0:

                LOGGER.debug("terminal node:")
                result.update({"score": self.heuristic.score(node.data['board'])})
                LOGGER.debug("result:")
                LOGGER.debug(result)
                return result
            new_data = expand(node.data)
            if new_data:
                for data in new_data:
                    LOGGER.debug("adding child: %s" % data)
                    node.add_child(data)
            else:
                LOGGER.debug("terminal node:")
                result.update({"score": self.heuristic.score(node.data['board'])})
                LOGGER.debug("result:")
                LOGGER.debug(result)
                return result
            if max_turn:
                best_value = {'score': neg_inf-1}
                for child in node.children:
                    states = [best_value, __min_max_prunning(child, _depth-1, alpha, beta, False)]
                    LOGGER.debug("selecting max from %d state:" % len(states))
                    LOGGER.debug(os.linesep.join(map(str, states)))
                    best_value = max(
                        states,
                        key=lambda x: x['score']
                    )
                    alpha = max(alpha, best_value['score'])
                    if beta <= alpha:
                        # LOGGER.debug("prunning occurred a:%d, b:%d" % (alpha, beta))
                        break
                return best_value
            else:
                best_value = {'score': pos_inf+1}
                for child in node.children:
                    states = [best_value, __min_max_prunning(child, _depth-1, alpha, beta, True)]
                    LOGGER.debug("selecting min from %d state:" % len(states))
                    LOGGER.debug(os.linesep.join(map(str, states)))
                    best_value = min(
                        states,
                        key=lambda x: x['score']
                    )
                    beta = min(beta, best_value['score'])
                    if beta <= alpha:
                        break
                return best_value

        val = __min_max_prunning(tree, depth)
        LOGGER.debug("recommended for %s: %s" % (self, val))
        return val


class NaiveHeuristic(BaseHeuristic):
    def score(self, board):
        if board.get_winner():
            if board.get_winner() == self.player:
                return POS_INF
            else:
                return NEG_INF
        return 1


class OpenEndedRunHeuristic(BaseHeuristic):
    def score(self, board):
        if board.get_winner():
            if board.get_winner() == self.player:
                return POS_INF
            else:
                return NEG_INF

        def score_piece(_row, _col, p, running_score=1, direction=None):
            if not 0 <= _row < len(board.board):
                return 0
            if not 0 <= _col < len(board.board[_row]):
                return 0
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
            piece = board.board[_row][_col]
            if not piece:
                return running_score
            if not piece.owner is p:
                # location owned by someone else
                return 0
            if piece.owner is p:
                # this is our piece, expand
                if not direction:
                    # start all directions
                    score_map = map(
                        lambda x: running_score * score_piece(
                            _row+x[0], _col+x[1], p, running_score+1, x
                        ), directions
                    )
                    return sum(score_map)
                else:
                    # use direction set in previous frame
                    return running_score * score_piece(
                        _row+direction[0], _col+direction[1], p, running_score+1, direction
                    )
            assert False
        # we recursively value pieces located with option to continue
        my_score = 0
        his_score = 0
        players = board.players[:]
        players.remove(self.player)
        him = players[0]
        for row in range(board.rows):
            # s = ""
            for col in range(board.columns):
                ms = score_piece(row, col, self)
                hs = score_piece(row, col, him)
                my_score += ms
                his_score += hs
                # s += "%d|%d," % (ms, hs)
                # LOGGER.debug(s)
        return my_score - his_score


class Piece(object):

    def __init__(self, x, y, owner):
        self.owner = owner
        self.location = (x, y,)

    def __str__(self):
        return "[Piece at %s taken by %s]" % (self.location, self.owner)


class TestNInARowGame(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple(self):
        self.game = Game(2, 2, 2)
        p1, p2 = AbstractPlayer("Reut"), AbstractPlayer("Eilit")
        self.game.add_player(p1)
        self.game.add_player(p2)
        self.game.start()


