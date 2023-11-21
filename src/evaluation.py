from helpers import *
from psqt import *

# External
import chess


class Evaluation:
    @staticmethod
    def eval_side(board: chess.Board, color: chess.Color) -> int:
        occupied = board.occupied_co[color]

        material = 0
        psqt = 0

        # loop over all set bits
        while occupied:
            # find the least significant bit
            square = lsb(occupied)

            piece = board.piece_type_at(square)

            # add material
            material += piece_values[piece]

            # add piece square table value
            psqt += (
                list(reversed(psqt_values[piece]))[square]
                if color == chess.BLACK
                else psqt_values[piece][square]
            )

            # remove lsb
            occupied = poplsb(occupied)

        return material + psqt

    @staticmethod
    def evaluate(board: chess.Board) -> int:
        return Evaluation.eval_side(board, chess.WHITE) - Evaluation.eval_side(
            board, chess.BLACK
        )
