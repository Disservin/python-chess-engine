# python-chess-engine

A UCI Chess Engine written in Python with python-chess.
I tried to keep the code relatively small while create a working engine that features the basics of all engines.

### Features
* Alphabeta Search
* Move ordering 
* Transposition Table
* Material and PSQT Evaluation
* Null move pruning

It also features python type hints.

### Run
```
python ./main.py
```

### Executable

On windows you can run `make-exe.bat` which should create the engine in `./build`.

### Python Version
Python 3.10+
