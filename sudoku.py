# Playing with sudoku
import numpy as np
import os, logging
from typing import Tuple, Literal


def get_idx(
    row_idx: int, col_idx: int
) -> Tuple[Literal[0, 1, 2], Literal[0, 1, 2], Literal[0, 1, 2], Literal[0, 1, 2]]:
    """Get numpy indices from the more user-friendly row/column system"""
    assert 0 <= row_idx <= 8 and 0 <= col_idx <= 8, "Invalid index number!"
    if 0 <= row_idx <= 2:
        innerRow = row_idx
        cellRows = 0
    elif 3 <= row_idx <= 5:
        innerRow = row_idx - 3
        cellRows = 1
    elif 6 <= row_idx <= 8:
        innerRow = row_idx - 6
        cellRows = 2
    if 0 <= col_idx <= 2:
        elem = col_idx
        cell = 0
    elif 3 <= col_idx <= 5:
        elem = col_idx - 3
        cell = 1
    elif 6 <= col_idx <= 8:
        elem = col_idx - 6
        cell = 2
    return cellRows, cell, innerRow, elem


def set_value(row: int, col: int, board: np.ndarray, value: int) -> np.ndarray:
    """Makes a copy of boad and returns it with modified (row,col) to `value`"""
    out_board = board.copy()
    out_board[get_idx(row, col)] = value
    return out_board


def makeBoard(rollback_factor: int = 8):
    """Generates 3x3 Sudoku board that follows all rules"""
    init_board = np.random.randint(1, 9, size=(3, 3, 3, 3))
    init_board = np.zeros((3, 3, 3, 3))
    row_idx, col_idx = 0, 0
    while row_idx < 3 * 3:
        while col_idx < 3 * 3:
            possible_values = [i for i in range(10)]
            val = 0
            while not check_legal(row_idx, col_idx, init_board):
                if len(possible_values) == 0:
                    # No values work for current cell => Need to roll back a few times and retry
                    rollbacks = min(rollback_factor, col_idx + row_idx * 8)
                    for i in range(rollbacks):
                        init_board = set_value(row_idx, col_idx, init_board, value=0)
                        if col_idx > 0:
                            col_idx -= 1
                        else:
                            row_idx -= 1
                            col_idx = 8
                    possible_values = [i for i in range(10)]
                    val = 0
                else:
                    possible_values.remove(val)
                    if len(possible_values) == 0:
                        continue
                    val = np.random.choice(possible_values)
                    init_board = set_value(row_idx, col_idx, init_board, val)
            col_idx += 1
        row_idx += 1
        col_idx = 0
    return init_board


def displayBoard(board: np.ndarray) -> None:
    """Creates readable string from board object and prints"""
    ret = ""
    rowNum = 0
    lineLength = 3 * board.shape[0] * board.shape[2] + (board.shape[1] - 1)

    # Print column numbers
    ret += " " * 2
    for colNum in range(board.shape[0] * board.shape[2]):
        if not colNum % board.shape[2] and colNum != 0:
            ret += f"  {colNum} "
        else:
            ret += f" {colNum} "
    ret += "\n"
    ret += "  " + "_" * lineLength + "\n"

    for i in range(board.shape[0]):
        for j in range(board.shape[2]):
            # Print row numbers
            ret += str(rowNum) + "|"
            rowNum += 1
            for k in range(board.shape[1]):
                for value in board[i, k, j, :]:
                    ret += f" {int(value)} "
                ret += "|"
            ret += "\n"
        ret += " |" + "-" * lineLength + "|\n"
    print(ret)


def check_legal(row_idx: int, col_idx: int, board: np.ndarray, verbose=False):
    """Checks if value in (row, col) for `board` follows all rules"""
    legal_flag = True
    cellRows, cell, innerRow, elem = get_idx(row_idx, col_idx)
    val = board[cellRows, cell, innerRow, elem]
    if val == 0:
        return False
    if verbose:
        print(f"{val = }")

    # Don't actually have to flatten atm but hey
    current_cell_values = board[cellRows, cell, :, :].flatten()
    horizontal_to_val = board[cellRows, :, innerRow, :].flatten()
    vertical_to_val = board[:, cell, :, elem].flatten()
    logger_msgs = [
        f"Several instances of value {val} " + a
        for a in ("in cell", "horizontally", "vertically")
    ]
    for i, area in enumerate((current_cell_values, horizontal_to_val, vertical_to_val)):
        if np.count_nonzero(area == val) > 1:
            if verbose:
                logging.debug(logger_msgs[i])
            legal_flag = False
    return legal_flag


def hide_portion_of_board(board, difficulty: float):
    """Masks approx. `difficulty`% to zeros in a new board"""
    num_to_hide = int(np.prod(board.shape) * difficulty)
    hidden_board = board.copy()
    ind = np.random.randint(0, 9, (num_to_hide, 2))
    for i in range(num_to_hide):
        hidden_board = set_value(ind[i, 0], ind[i, 1], hidden_board, 0)
    return hidden_board


def load_from_file():
    fn = input("Enter filename, leave blank to search for current directory: ")
    if fn == "":
        found = [0, 0]
        for file in os.listdir("."):
            if file.endswith(".npy"):
                print(f"Found file {file}. Trying to load")
                if file.endswith("_usr.npy"):
                    found[0] += 1
                    user_board = np.load(file)
                elif file.endswith("_sol.npy"):
                    found[1] += 1
                    complete_board = np.load(file)
        if not all(found) == 1:
            logging.warn(
                "Warning: Lookup did not find (exactly) one solution and user progress. Incorrect boards may have been loaded."
            )
    return user_board, complete_board


def game(difficulty: float, hints: bool) -> None:
    complete_board = makeBoard()
    print("Welcome to Sudoku!")
    print(
        "Set a value by writing input on the form '<row>,<col>,<val>', e.g. 1,5,3 to set '3' to row 1 and column 5"
    )
    print("Choose value '0' to undo a change.")
    user_board = hide_portion_of_board(complete_board, difficulty)
    displayBoard(complete_board)  # For debugging
    displayBoard(user_board)
    while user_board.all() != complete_board.all():
        action = input("What do you want to do? (play, save, load, exit)")
        while action not in ("play", "save", "load", "exit"):
            action = input("Invalid command. Try again: ")
        if action == "save":
            save_pth = input("What should it be saved as? ")
            np.save(save_pth + "_usr", user_board)
            np.save(save_pth + "_sol", complete_board)
            print("Successfully saved!")
        elif action == "load":
            user_board, complete_board = load_from_file()
        elif action == "play":
            reply = input("Set value to board, format '<row>,<col>,<val>': ")
            try:
                row, col, val = [int(i) for i in reply.split(",")]
            except:  # noqa
                print("Invalid format.")
                continue
            user_board = set_value(row, col, user_board, val)
            if hints:
                if not check_legal(row, col, user_board):
                    override_reply = input(
                        "I wouldn't do that if I were you.. Are you sure? (Y/N)"
                    )
                    if override_reply.lower() == "n":
                        user_board = set_value(row, col, user_board, 0)
            displayBoard(user_board)
        elif action == "exit":
            break
    if user_board.all() == complete_board.all():
        print("Congrats, you won!")
    else:
        print("Sad to see you go. Let's play again soon!")


game(0.1, True)
