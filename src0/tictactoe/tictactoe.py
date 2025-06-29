"""
Tic Tac Toe Player
"""

import math

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    count_x = sum(cell == "X" for row in board for cell in row)
    count_o = sum(cell == "O" for row in board for cell in row)
    if count_x > count_o:
        return O
    else:
        return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    actions = [(i, j) for i in range(3) for j in range(3) if board[i][j] == EMPTY]
    return set(actions)


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    
    i, j = action
    if (i < 0 or i >= 3 or j < 0 or j >= 3 or board[i][j] is not EMPTY):
        raise ValueError("Invalid action")
    new_board = [row.copy() for row in board]
    new_board[i][j] = player(board)
    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    for row in board: # Look for horizontal wins
        if row[0] == row[1] == row[2] != EMPTY:
            return row[0]
    for col in range(3): # Look for vertical wins
        if board[0][col] == board[1][col] == board[2][col] != EMPTY:
            return board[0][col]
    # Now look for diagonal wins
    if board[0][0] == board[1][1] == board[2][2] != EMPTY:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != EMPTY:
        return board[0][2]
    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    If someone has won or the board is full, the game is over.
    """
    return winner(board) is not None or all(cell is not EMPTY for row in board for cell in row) 


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    if winner(board) == X:
        return 1
    elif winner(board) == O:
        return -1
    else:
        return 0

#	In max_value, if v >= no_more_than, we prune — Min won’t allow this branch to be chosen, so Max doesn’t need to look further.
#	In min_value, if v <= no_less_than, we prune — Max has a better option already, so Min doesn’t need to look further.

def minimax(board):
    if terminal(board):
        return None

    turn = player(board)
    best_move = None

    if turn == X:
        best_score = float('-inf')
        no_less_than = float('-inf')  # alpha

        for action in actions(board):
            score = min_value(result(board, action), no_less_than, float('inf'))
            if score > best_score:
                best_score = score
                best_move = action
                no_less_than = max(no_less_than, best_score)

    else:  # turn == O
        best_score = float('inf')
        no_more_than = float('inf')  # beta

        for action in actions(board):
            score = max_value(result(board, action), float('-inf'), no_more_than)
            if score < best_score:
                best_score = score
                best_move = action
                no_more_than = min(no_more_than, best_score)

    return best_move

# min will prune branches where the value is less than or equal to no_less_than, 
# and max will prune branches where the value is greater than or equal to no_more_than.
def max_value(board, no_less_than, no_more_than):
    if terminal(board):
        return utility(board)

    v = float('-inf')
    for action in actions(board):
        v = max(v, min_value(result(board, action), no_less_than, no_more_than))
        no_less_than = max(no_less_than, v)
        if v >= no_more_than:
            break  # prune
    return v


def min_value(board, no_less_than, no_more_than):
    if terminal(board):
        return utility(board)

    v = float('inf')
    for action in actions(board):
        v = min(v, max_value(result(board, action), no_less_than, no_more_than))
        no_more_than = min(no_more_than, v)
        if v <= no_less_than:
            break  # prune
    return v
