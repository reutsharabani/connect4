from random import choice
import os
import logging
from AI import MinMaxStrategy, AvailableVictoriesHeuristic

LOGGER = logging.getLogger("connect4-logic")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)
LOGGER.addHandler(sh)
LOGGER.setLevel(logging.WARN)


def make_directions(rows, columns, goal):
    return ((0, 1, xrange(rows), xrange(columns - goal)),
            (1, 0, xrange(rows - goal), xrange(columns)),
            (1, 1, xrange(rows - goal), xrange(columns - goal)),
            (-1, 1, xrange(goal, rows), xrange(columns - goal)))


class Game(object):
    def __init__(self, players, rows, columns, goal):
        # rowstep, colstep, row-xrange, col-xrange
        self.board = Board(players, rows, columns, goal)
        self.goal = goal


class LocationTakenError(Exception):
    pass


class NotYourTurnError(Exception):
    pass


class NoMovesPlayedError(Exception):
    pass


class BoardWonError(Exception):
    pass


class Board(object):
    NEGATIVE_BOARD = object()
    POSITIVE_BOARD = object()

    def __init__(self, players, rows=6, columns=7, goal=24, tipheuristic=AvailableVictoriesHeuristic,
                 moves=()):
        self.moves = moves
        self.rows = rows
        self.columns = columns
        self.goal = goal
        # tip's column
        self.tip_strategy = lambda player: MinMaxStrategy(tipheuristic(player)).get_move(self, 4)
        self.board = [tuple(None for _ in range(columns)) for _ in range(rows)]

        self.players = players
        self.current_player = choice(self.players)

        self.directions = make_directions(self.rows, self.columns, self.goal)

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
            new_row, new_col, player, left - 1, direction
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
        if len(list(self.valid_moves_iterator)) == 0:
            return "draw"
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
            LOGGER.debug("row: %d, column: %d" % (row, _column))
            _piece = self.board[row][_column]

            LOGGER.debug("Trying to put %s in (%d, %d) - currently: %s" % (_player, row, _column, _piece))
            if not _piece:
                LOGGER.debug("old row: %r, changing column: %d", self.board[row], _column)
                self.board[row] = tuple(
                    piece if not column == _column else Piece(row, _column, _player) for column, piece in
                    enumerate(self.board[row]))
                LOGGER.debug("new row: %r", self.board[row])
                self.move_turn_to_next_player()
                self.moves = self.moves + ((self.current_player, row, _column,),)
                return row, _column

        raise LocationTakenError()

    def undo(self):
        if len(self.moves) > 0:
            tempmoves = list(self.moves)
            player, row, column = tempmoves.pop()
            self.moves = tuple(tempmoves)
            self.board[row] = tuple(
                piece if not column == _column else None for _column, piece in
                enumerate(self.board[row]))
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
    def nrun_iterator(self):
        for direction in self.directions:
            for row in direction[2]:
                for col in direction[3]:
                    yield ((row + direction[0] * x, col + direction[1] * x) for x in xrange(self.goal))

    @property
    def valid_moves_iterator(self):
        for i in xrange(len(self.board[0])):
            # check if column has room
            if self.board[0][i] is None:
                yield i

    def copy(self, move):

        LOGGER.debug("Creating copy of board with move: %s", str(move))
        _board = Board(
            self.players, rows=self.rows, columns=self.columns, goal=self.goal, moves=self.moves
        )

        # these are not set correctly on initialization
        _board.board = [x for x in self.board]
        _board.current_player = self.current_player
        _board.put_one(move)
        return _board

    def simulate_move(self, move):
        LOGGER.debug("simulating move: %s" % move)
        new_board = self.copy(move)
        LOGGER.debug("%d X %d board initialized: %s" % (new_board.rows, new_board.columns, str(new_board)))
        return new_board


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
        # return board.simulate_move(move)


class HumanPlayer(AbstractPlayer):
    def get_move(self, board, column):
        LOGGER.debug("Human player playing column: %d" % column)
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
        LOGGER.debug("Computer player playing column: %d" % column)
        winner = board.get_winner()
        if winner:
            raise BoardWonError("Board already won by %s" % winner)
        if board.is_full():
            raise BoardFullError("Board full. Undo or quit.")
        state = self.strategy.get_move(board, startdepth=self.difficulty)
        moves = tuple(s[2] for s in state.moves)
        LOGGER.debug("Found moves: %s" % os.linesep.join(map(str, moves)))
        return moves[len(board.moves):][0]


class Piece(object):
    def __init__(self, x, y, owner):
        self.owner = owner
        self.location = (x, y,)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[Piece at %s taken by %s]" % (self.location, self.owner)

    def __hash__(self):
        return hash((self.owner.id, self.location))

    def __eq__(self, other):
        return other and isinstance(other, Piece) and (
            self.owner.id == other.owner.id
        ) and (self.location == other.location)
