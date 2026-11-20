#include <bits/stdc++.h>
using namespace std;

// Counts pairs (i < j) with values[i] + values[j] == target.
long long countTargetPairs(const vector<long long>& values, long long target) {
    unordered_map<long long, long long> frequency;
    long long result = 0;
    for (const long long value : values) {
        auto it = frequency.find(target - value);
        if (it != frequency.end()) {
            result += it->second;
        }
        frequency[value] += 1;
    }
    return result;
}

int main() {
    int n;
    long long target;
    cin >> n >> target;
    vector<long long> values(n);
    for (auto& v : values) cin >> v;
    cout << countTargetPairs(values, target) << '\n';
    return 0;
}
