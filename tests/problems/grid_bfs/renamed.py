from collections import deque

# BFS from the top-left cell to the bottom-right one


def bfs(board, rows, cols):
    steps = [[-1] * cols for _ in range(rows)]
    steps[0][0] = 0
    queue = deque([(0, 0)])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            a, b = x + dx, y + dy
            # stay inside, open cells only, first visit wins
            if 0 <= a < rows and 0 <= b < cols and board[a][b] == '.' and steps[a][b] == -1:
                steps[a][b] = steps[x][y] + 1
                queue.append((a, b))
    return steps[rows - 1][cols - 1]


rows, cols = map(int, input().split())
board = [input() for _ in range(rows)]
print(bfs(board, rows, cols))
