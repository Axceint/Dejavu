#include <cstdio>
int a[200005];
int main() {
    int n, k;
    scanf("%d %d", &n, &k);
    for (int i = 0; i < n; ++i) scanf("%d", &a[i]);
    long long c = 0;
    for (int i = 0; i < n; ++i)
        for (int j = i + 1; j < n; ++j)
            if (a[i] + a[j] == k) ++c;
    printf("%lld\n", c);
    return 0;
}
