from helpers import *

# External
import chess
from enum import Enum

Flag = Enum("Flag", ["NONEBOUND", "UPPERBOUND", "LOWERBOUND", "EXACTBOUND"])

"""
This is an entry in our TT, it saves
information about the score, flag and most
importantly the move.
"""


class TEntry:
    def __init__(self) -> None:
        self.key = 0
        self.depth = 0
        self.flag = Flag.NONEBOUND
        self.score = VALUE_NONE
        self.move = chess.Move.null()


class TranspositionTable:
    def __init__(self) -> None:
        # Higher values take rather long to initialize
        self.tt_size = 2**19 - 1
        self.transposition_table = [TEntry() for _ in range(self.tt_size)]

    # Calculate "array" index
    def ttIndex(self, key: int) -> int:
        return key % self.tt_size

    # store an entry in the TT
    def storeEntry(
        self, key: int, depth: int, flag: Flag, score: int, move: chess.Move, ply: int
    ) -> None:
        index = self.ttIndex(key)
        entry = self.transposition_table[index]

        # Replacement schema
        if entry.key != key or entry.move != move:
            entry.move = move

        if entry.key != key or flag == Flag.EXACTBOUND or depth + 4 > entry.depth:
            entry.depth = depth
            entry.score = self.scoreToTT(score, ply)
            entry.key = key
            entry.flag = flag

        # self.transposition_table[index] = entry

    def probeEntry(self, key: int) -> TEntry:
        index = self.ttIndex(key)
        entry = self.transposition_table[index]

        return entry

    # if we want to save correct mate scores we have to adjust the distance
    def scoreToTT(self, s: int, plies: int) -> int:
        if s >= VALUE_TB_WIN_IN_MAX_PLY:
            return s + plies
        else:
            if s <= VALUE_TB_LOSS_IN_MAX_PLY:
                return s - plies
            else:
                return s

    # undo the previous adjustment
    def scoreFromTT(self, s: int, plies: int) -> int:
        if s >= VALUE_TB_WIN_IN_MAX_PLY:
            return s - plies
        else:
            if s <= VALUE_TB_LOSS_IN_MAX_PLY:
                return s + plies
            else:
                return s
