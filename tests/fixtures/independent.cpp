#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    int mx = 0;
    for (int &v : a) { cin >> v; if (v > mx) mx = v; }
    vector<bool> composite(mx + 1, false);
    for (int p = 2; (long long)p * p <= mx; ++p)
        if (!composite[p])
            for (int q = p * p; q <= mx; q += p) composite[q] = true;
    long long s = 0;
    int c = 0;
    for (int v : a)
        if (v >= 2 && !composite[v]) { c++; s += v; }
    printf("%d %lld\n", c, s);
}
