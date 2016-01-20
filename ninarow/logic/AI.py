# -*- coding: utf8 -*-
import ninarow.logic.game


class NaiveHeuristic(object):
    pass


""" based on:
# 01 function alphabeta(node, depth, α, β, maximizingPlayer)
# 02      if depth = 0 or node is a terminal node
# 03          return the heuristic value of node
# 04      if maximizingPlayer
# 05          v := -∞
# 06          for each child of node
# 07              v := max(v, alphabeta(child, depth - 1, α, β, FALSE))
# 08              α := max(α, v)
# 09              if β ≤ α
# 10                  break (* β cut-off *)
# 11          return v
# 12      else
# 13          v := ∞
# 14          for each child of node
# 15              v := min(v, alphabeta(child, depth - 1, α, β, TRUE))
# 16              β := min(β, v)
# 17              if β ≤ α
# 18                  break (* α cut-off *)
# 19          return v
"""


class MinMaxStrategy(object):
    def __init__(self, heuristic):
        self.heuristic = heuristic

    def get_move(self, board, startdepth):
        maxplayer = board.current_player

        def __abprun(node, depth, a, b):
            print "prunning..."
            if depth == 0 or board.get_winner():
                return node

            if node.current_player is maxplayer:
                # maximize
                v = ninarow.logic.game.Board.NEGATIVE_BOARD
                for move in board.valid_moves_iterator:
                    v = max(v, __abprun(board.simulate_move(move), depth - 1, a, b), key=self.heuristic.value)
                    a = max(a, v, key=self.heuristic.value)
                    if b <= a:
                        break
                return v
            # minimize
            v = ninarow.logic.game.Board.POSITIVE_BOARD
            for move in board.valid_moves_iterator:
                v = min(v, __abprun(board.simulate_move(move), depth - 1, a, b), key=self.heuristic.value)
                b = min(a, v, key=self.heuristic.value)
                if b <= a:
                    break
            return v

        return __abprun(board, startdepth, ninarow.logic.game.Board.NEGATIVE_BOARD,
                        ninarow.logic.game.Board.POSITIVE_BOARD)


def unruined_nruns(board):
    for nrun in board.nrun_iterator:
        players_on_nrun = tuple(board.get_piece(*location) for location in nrun)
        owners = set(players_on_nrun)
        if len(owners) == 1:
            yield nrun, players_on_nrun.count(next(owners.__iter__()))


class PossibleVictoryHeuristic(object):
    def __init__(self, player):
        self.player = player

    def value(self, board):
        if board is ninarow.logic.game.Board.POSITIVE_BOARD:
            return 9999
        if board is ninarow.logic.game.Board.NEGATIVE_BOARD:
            return -9999
        # TODO: scale with run length and strength (already taken pieces)
        return sum(map(lambda run_player: -2 if run_player[1] is not self.player else 1, unruined_nruns(board)))
