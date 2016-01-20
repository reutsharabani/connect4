# -*- coding: utf8 -*-
import ninarow.logic.game
import os


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
        players_on_nrun = tuple(board.get_piece(*location).owner for location in nrun if board.get_piece(*location) is not None)
        owners = set(players_on_nrun)
        if len(owners) == 1:
            owner = next(owners.__iter__())
            yield nrun, players_on_nrun.count(owner), owner


class PossibleVictoryHeuristic(object):
    def __init__(self, player):
        self.player = player

    def value(self, board):
        if board is ninarow.logic.game.Board.POSITIVE_BOARD:
            return 9999
        if board is ninarow.logic.game.Board.NEGATIVE_BOARD:
            return -9999
        # TODO: scale with run length and strength (already taken pieces)
        unruinedruns = list(unruined_nruns(board))
        print os.linesep.join(str(l) for l in unruinedruns)

        def __value(run, count, player):
            result = -2 if player is not self.player else 1
            print "heuristic result: %d" % result
            return result

        return sum(map(lambda args: __value(*args), unruined_nruns(board)))
