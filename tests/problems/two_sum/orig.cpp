#include <iostream>
#include <unordered_map>
using namespace std;

int main() {
    int n;
    long long k;
    cin >> n >> k;
    unordered_map<long long, long long> seen;
    long long pairs = 0;
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        pairs += seen[k - x];
        seen[x]++;
    }
    cout << pairs << endl;
}
