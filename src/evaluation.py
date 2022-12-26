from helpers import *
from psqt import *

# External
import chess


class Evaluation:
    def eval_side(self, board: chess.Board, color: chess.Color) -> int:
        occupied = board.occupied_co[color]

        material = 0
        psqt = 0

        # loop over all set bits
        while occupied:
            # find the least significant bit
            square = lsb(occupied)

            piece = board.piece_type_at(square)
            material += piece_values[piece]

            psqt += (
                list(reversed(psqt_values[piece]))[square]
                if color == chess.BLACK
                else psqt_values[piece][square]
            )

            occupied = poplsb(occupied)

        return material + psqt

    def evaluate(self, board: chess.Board) -> int:
        return self.eval_side(board, board.turn) - self.eval_side(board, not board.turn)
