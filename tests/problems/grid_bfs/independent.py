import sys


def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    g = data[2:2 + n]
    target = (n - 1, m - 1)
    seen = {(0, 0)}
    layer = [(0, 0)]
    steps = 0
    while layer:
        if target in seen:
            return steps
        nxt = []
        for r, c in layer:
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < n and 0 <= nc < m and g[nr][nc] == '.' and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    nxt.append((nr, nc))
        layer = nxt
        steps += 1
    return -1


print(main())
