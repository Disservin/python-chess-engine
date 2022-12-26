import time
import tt as TT
import evaluation as Eval
import psqt as PQST

# External
import chess
import chess.polyglot
from helpers import *
from limits import *
from sys import stdout


class Search:
    def __init__(self, board: chess.Board) -> None:
        self.board = board
        self.transposition_table = TT.TranspositionTable()
        self.eval = Eval.Evaluation()

        self.pvLength = [0] * MAX_PLY
        self.pvTable = [[chess.Move.null()] * MAX_PLY for _ in range(MAX_PLY)]

        self.nodes = 0
        self.searchStartTime = 0

        self.limit = Limits(0, MAX_PLY, 0)

        self.stop = False
        self.checks = CHECK_RATE

        self.hashHistory = []

        # History Table
        self.htable = [[[0 for x in range(64)] for y in range(64)] for z in range(2)]

    def qsearch(self, alpha: int, beta: int, ply: int) -> int:
        if self.stop or self.checkTime():
            return 0

        # Dont search higher than MAX_PLY
        if ply >= MAX_PLY:
            return self.eval.evaluate(self.board)

        # staticEval
        bestValue = self.eval.evaluate(self.board)

        if bestValue >= beta:
            return bestValue

        if bestValue > alpha:
            alpha = bestValue

        # Sort the moves, the highest score should come first
        moves = sorted(
            self.board.generate_legal_captures(),
            key=lambda move: self.scoreQMove(move),
            reverse=True,
        )

        for move in moves:
            self.nodes += 1

            captured = self.board.piece_type_at(move.to_square)

            # Delta Pruning
            if (
                PQST.piece_values[captured] + 400 + bestValue < alpha
                and not move.promotion
            ):
                continue

            # Make move
            self.board.push(move)

            score = -self.qsearch(-beta, -alpha, ply + 1)

            # Unmake move
            self.board.pop()

            if score > bestValue:
                bestValue = score

                if score > alpha:
                    alpha = score

                    if score >= beta:
                        break

        return bestValue

    def absearch(self, alpha: int, beta: int, depth: int, ply: int) -> int:
        if self.checkTime():
            return 0

        # Dont search higher than MAX_PLY
        if ply >= MAX_PLY:
            return self.eval.evaluate(self.board)

        self.pvLength[ply] = ply

        RootNode = ply == 0

        hashKey = self.getHash()

        if not RootNode:
            if self.isRepetition(hashKey):
                return -5

            if self.board.halfmove_clock >= 100:
                return 0

            # Mate distance pruning
            alpha = max(alpha, mated_in(ply))
            beta = min(beta, mate_in(ply + 1))
            if alpha >= beta:
                return alpha

        # Jump into qsearch
        if depth <= 0:
            return self.qsearch(alpha, beta, ply)

        # Transposition Table probing
        tte = self.transposition_table.probeEntry(hashKey)
        ttHit = hashKey == tte.key
        ttMove = tte.move if ttHit else chess.Move.null()

        # Adjust score
        ttScore = (
            self.transposition_table.scoreFromTT(tte.score, ply)
            if ttHit
            else VALUE_NONE
        )

        if not RootNode and tte.depth >= depth and ttHit:
            if tte.flag == TT.Flag.EXACTBOUND:
                return ttScore
            elif tte.flag == TT.Flag.LOWERBOUND:
                alpha = max(alpha, ttScore)
            elif tte.flag == TT.Flag.UPPERBOUND:
                beta = min(beta, ttScore)

            if alpha >= beta:
                return ttScore

        inCheck = self.board.is_check()

        # Null move pruning
        if depth >= 3 and not inCheck:
            self.board.push(chess.Move.null())

            score = -self.absearch(-beta, -beta + 1, depth - 2, ply + 1)

            self.board.pop()

            if score >= beta:

                if score >= VALUE_TB_WIN_IN_MAX_PLY:
                    score = beta

                return score

        oldAlpha = alpha
        bestScore = -VALUE_INFINITE
        bestMove = chess.Move.null()
        madeMoves = 0

        # Sort the moves, the highest score should come first
        moves = sorted(
            self.board.legal_moves,
            key=lambda move: self.scoreMove(move, ttMove),
            reverse=True,
        )

        for move in moves:
            madeMoves += 1
            self.nodes += 1

            # Make move
            self.board.push(move)
            self.hashHistory.append(hashKey)

            # Search
            score = -self.absearch(-beta, -alpha, depth - 1, ply + 1)

            # Unmake move
            self.board.pop()
            self.hashHistory.pop()

            if score > bestScore:
                bestScore = score
                bestMove = move

                # update PV
                self.pvTable[ply][ply] = move

                for i in range(ply + 1, self.pvLength[ply + 1]):
                    self.pvTable[ply][i] = self.pvTable[ply + 1][i]

                self.pvLength[ply] = self.pvLength[ply + 1]

                if score > alpha:
                    # update alpha!
                    alpha = score

                    if score >= beta:
                        # update history
                        if not self.board.is_capture(move):
                            bonus = depth * depth
                            hhBonus = (
                                bonus
                                - self.htable[self.board.turn][move.from_square][
                                    move.to_square
                                ]
                                * abs(bonus)
                                / 16384
                            )

                            self.htable[self.board.turn][move.from_square][
                                move.to_square
                            ] += hhBonus
                        break

        # No moves were played so its checkmate or stalemate
        if madeMoves == 0:
            if inCheck:
                return mated_in(ply)
            else:
                return 0

        # Calculate bound and save position in TT

        bound = TT.Flag.NONEBOUND

        if bestScore >= beta:
            bound = TT.Flag.LOWERBOUND
        else:
            if alpha != oldAlpha:
                bound = TT.Flag.EXACTBOUND
            else:
                bound = TT.Flag.UPPERBOUND

        if not self.checkTime():
            # Store in TT
            self.transposition_table.storeEntry(
                hashKey, depth, bound, bestScore, bestMove, ply
            )

        return bestScore

    def iterativeDeepening(self) -> None:

        self.nodes = 0

        score = -VALUE_INFINITE
        bestmove = chess.Move.null()

        # Start measuring time
        self.t0 = time.time_ns()

        # Iterative Deepening Loop
        for d in range(1, self.limit.limited["depth"] + 1):
            score = self.absearch(-VALUE_INFINITE, VALUE_INFINITE, d, 0)

            # Dont use completed depths result
            if self.stop or self.checkTime(True):
                break

            # Save bestmove
            bestmove = self.pvTable[0][0]

            # print info
            now = time.time_ns()
            stdout.write(self.stats(d, score, now - self.t0) + "\n")
            stdout.flush()

        # last attempt to get a bestmove
        if bestmove == chess.Move.null():
            bestmove = self.pvTable[0][0]

        # print bestmove
        stdout.write("bestmove " + str(bestmove) + "\n")
        stdout.flush()

    # Detect a repetition
    def isRepetition(self, key: int, draw: int = 1) -> bool:
        count = 0
        size = len(self.hashHistory)

        for i in range(size - 1, -1, -2):
            if i >= size - self.board.halfmove_clock:
                if self.hashHistory[i] == key:
                    count += 1
                if count == draw:
                    return True

        return False

    # Most Valuable Victim - Least Valuable Aggressor
    def mvvlva(self, move: chess.Move) -> int:
        mvvlva = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 105.0, 104.0, 103.0, 102.0, 101.0, 100.0],
            [0, 205.0, 204.0, 203.0, 202.0, 201.0, 200.0],
            [0, 305.0, 304.0, 303.0, 302.0, 301.0, 300.0],
            [0, 405.0, 404.0, 403.0, 402.0, 401.0, 400.0],
            [0, 505.0, 504.0, 503.0, 502.0, 501.0, 500.0],
            [0, 605.0, 604.0, 603.0, 602.0, 601.0, 600.0],
        ]

        from_square = move.from_square
        to_square = move.to_square
        attacker = self.board.piece_type_at(from_square)
        victim = self.board.piece_type_at(to_square)

        # En passant
        if victim is None:
            victim = 1
        return mvvlva[victim][attacker]

    # assign a score to moves in qsearch
    def scoreQMove(self, move: chess.Move) -> int:
        return self.mvvlva(move)

    # assign a score to normal moves
    def scoreMove(self, move: chess.Move, ttMove: chess.Move) -> int:
        if move == ttMove:
            return 1_000_000
        elif self.board.is_capture(move):
            # make sure captures are ordered higher than quiets
            return 32_000 + self.mvvlva(move)
        return self.htable[self.board.turn][move.from_square][move.to_square]

    def getHash(self) -> int:
        return chess.polyglot.zobrist_hash(self.board)

    def checkTime(self, iter: bool = False) -> bool:
        if self.stop:
            return True

        if (
            self.limit.limited["nodes"] != 0
            and self.nodes >= self.limit.limited["nodes"]
        ):
            return True

        if self.checks > 0 and not iter:
            self.checks -= 1
            return False

        self.checks = CHECK_RATE

        if self.limit.limited["time"] == 0:
            return False

        timeNow = time.time_ns()
        if (timeNow - self.t0) / 1_000_000 > self.limit.limited["time"]:
            return True

    # Build PV
    def getPV(self) -> str:
        pv = ""

        for i in range(0, self.pvLength[0]):
            pv += " " + str(self.pvTable[0][i])

        return pv

    # Convert mate scores
    def convert_score(self, score: int) -> str:
        if score >= VALUE_MATE_IN_PLY:
            return "mate " + str(
                ((VALUE_MATE - score) // 2) + ((VALUE_MATE - score) & 1)
            )
        elif score <= VALUE_MATED_IN_PLY:
            return "mate " + str(
                -((VALUE_MATE + score) // 2) + ((VALUE_MATE + score) & 1)
            )
        else:
            return "cp " + str(score)

    # Print uci info
    def stats(self, depth: int, score: int, time: int) -> str:
        time_in_ms = int(time / 1_000_000)
        time_in_seconds = max(1, time_in_ms / 1_000)
        info = (
            "info depth "
            + str(depth)
            + " score "
            + str(self.convert_score(score))
            + " nodes "
            + str(self.nodes)
            + " nps "
            + str(int(self.nodes / time_in_seconds))
            + " time "
            + str(round(time / 1_000_000))
            + " pv"
            + self.getPV()
        )
        return info

    # Reset search stuff
    def reset(self) -> None:
        self.pvLength[0] = 0
        self.nodes = 0
        self.t0 = 0
        self.stop = False
        self.checks = CHECK_RATE
        self.hashHistory = []
        self.htable = [[[0 for x in range(64)] for y in range(64)] for z in range(2)]


# Run search.py instead of main.py if you want to profile it!
if __name__ == "__main__":
    board = chess.Board()
    search = Search(board)

    search.limit.limited["depth"] = 6

    search.iterativeDeepening()
