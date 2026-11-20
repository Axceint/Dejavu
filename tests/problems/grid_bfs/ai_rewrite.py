from collections import deque
from typing import List

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def in_bounds(row: int, col: int, rows: int, cols: int) -> bool:
    return 0 <= row < rows and 0 <= col < cols


def find_shortest_path(maze: List[str], rows: int, cols: int) -> int:
    """Breadth-first search from the top-left to the bottom-right cell."""
    distance = [[-1 for _ in range(cols)] for _ in range(rows)]
    distance[0][0] = 0
    frontier = deque()
    frontier.append((0, 0))
    while frontier:
        row, col = frontier.popleft()
        for d_row, d_col in DIRECTIONS:
            next_row, next_col = row + d_row, col + d_col
            if not in_bounds(next_row, next_col, rows, cols):
                continue
            if maze[next_row][next_col] != '.' or distance[next_row][next_col] != -1:
                continue
            distance[next_row][next_col] = distance[row][col] + 1
            frontier.append((next_row, next_col))
    return distance[rows - 1][cols - 1]


if __name__ == "__main__":
    rows, cols = map(int, input().split())
    maze = [input().strip() for _ in range(rows)]
    print(find_shortest_path(maze, rows, cols))
