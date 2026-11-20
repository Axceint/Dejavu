#include <cstdio>
#include <cstring>
char g[1005][1005];
int d[1005 * 1005], qu[1005 * 1005];
int main() {
    int n, m;
    scanf("%d %d", &n, &m);
    for (int i = 0; i < n; i++) scanf("%s", g[i]);
    memset(d, -1, sizeof d);
    int head = 0, tail = 0;
    qu[tail++] = 0;
    d[0] = 0;
    while (head < tail) {
        int cur = qu[head++], r = cur / m, c = cur % m;
        if (r > 0 && g[r - 1][c] == '.' && d[cur - m] < 0) { d[cur - m] = d[cur] + 1; qu[tail++] = cur - m; }
        if (r + 1 < n && g[r + 1][c] == '.' && d[cur + m] < 0) { d[cur + m] = d[cur] + 1; qu[tail++] = cur + m; }
        if (c > 0 && g[r][c - 1] == '.' && d[cur - 1] < 0) { d[cur - 1] = d[cur] + 1; qu[tail++] = cur - 1; }
        if (c + 1 < m && g[r][c + 1] == '.' && d[cur + 1] < 0) { d[cur + 1] = d[cur] + 1; qu[tail++] = cur + 1; }
    }
    printf("%d\n", d[n * m - 1]);
}
