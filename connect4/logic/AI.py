# -*- coding: utf8 -*-
import connect4.logic.game
import os

import logging

LOGGER = logging.getLogger("connect4-AI")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)
LOGGER.addHandler(sh)
LOGGER.setLevel(logging.WARN)


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
        LOGGER.info("Fetching best move (level: %d)" % startdepth)
        maxplayer = board.current_player

        def __abprun(node, depth, a, b):
            LOGGER.debug("prunning...")
            if depth == 0 or node.get_winner():
                return node

            if node.current_player is maxplayer:
                # maximize
                v = connect4.logic.game.Board.NEGATIVE_BOARD
                # LOGGER.debug("Moves: %s" % str(list(node.valid_moves_iterator)))
                for move in node.valid_moves_iterator:
                    # LOGGER.info("Selected max move: %d, depth: %d" % (move, depth))
                    v = max(v, __abprun(node.simulate_move(move), depth - 1, a, b), key=self.heuristic.value)
                    a = max(a, v, key=self.heuristic.value)
                    if self.heuristic.value(b) <= self.heuristic.value(a):
                        # LOGGER.info("Pruned at maximize move %d (value: %d)", move, self.heuristic.value(b))
                        break

                LOGGER.info("max move: %s, %s" % (str([move[2] for move in a.moves]), str(a)))
                return a
            # minimize
            v = connect4.logic.game.Board.POSITIVE_BOARD
            # LOGGER.debug("Moves: %s" % str(list(node.valid_moves_iterator)))
            for move in node.valid_moves_iterator:
                # LOGGER.info("Selected min move: %d, depth: %d" % (move, depth))
                v = min(v, __abprun(node.simulate_move(move), depth - 1, a, b), key=self.heuristic.value)
                b = min(b, v, key=self.heuristic.value)
                if self.heuristic.value(b) <= self.heuristic.value(a):
                    # LOGGER.info("Pruned at minimize move %d (value: %d)", move, self.heuristic.value(b))
                    break
            LOGGER.info("min move: %s, %s" % (str([move[2] for move in b.moves]), str(b)))
            return b
        best = __abprun(board, min(startdepth, len(list(board.valid_moves_iterator))), connect4.logic.game.Board.NEGATIVE_BOARD,
                        connect4.logic.game.Board.POSITIVE_BOARD)
        LOGGER.info("Best move: %s (score: %d)" % (str(best), self.heuristic.value(best)))
        LOGGER.info("moves: %s)" % str(tuple(x[2] for x in best.moves)))
        return best


def nruns_with_owners(board):
    for nrun in board.nrun_iterator:
        nrun = list(nrun)
        players_on_nrun = tuple(board.get_piece(*location).owner for location in nrun if board.get_piece(*location) is not None)
        # LOGGER.debug("players on nrun: %s" % str(players_on_nrun))
        owners = set(players_on_nrun)
        yield nrun, owners


class AvailableVictoriesHeuristic(object):
    def __init__(self, player):
        self.player = player

    def value(self, board):
        if board is connect4.logic.game.Board.POSITIVE_BOARD:
            return 9999
        if board is connect4.logic.game.Board.NEGATIVE_BOARD:
            return -9999
        winner = board.get_winner()
        if winner:
            if winner is self.player:
                return 9998
            return -9998

        # TODO: scale with run length and strength (already taken pieces)

        def __value(run, owners):
            if len(owners) == 0:
                # available - we want it taken so -1
                return -1

            if len(owners) == 1:
                _owner = next(iter(owners))
                # bias towards ruining other player's runs
                taken_count = 0
                for x, y in run:
                    piece = board.get_piece(x, y)
                    if piece and piece.owner == _owner:
                        taken_count += 1

                if _owner == self.player:
                    return 2 ** taken_count
                return -(3 ** taken_count)

            if len(owners) > 1:
                # ruined...
                return 0

        score = 0
        for nrun_with_owners in nruns_with_owners(board):
            nrun = list(nrun_with_owners[0])
            v = __value(nrun, nrun_with_owners[1])
            # LOGGER.debug("nrun: %s, owners: %s, score: %s" % ([board.get_piece(x, y) for x, y in nrun], [owner.id for owner in nrun_with_owners[1]], v))
            score += v
        # LOGGER.debug("Value: %d", score)
        return score
