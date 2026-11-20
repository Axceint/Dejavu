#include <bits/stdc++.h>
using namespace std;

// Returns true when value is a prime number.
static bool is_prime_value(long long value) {
    if (value < 2) {
        return false;
    }
    for (long long d = 2; d * d <= value; ++d) {
        if (value % d == 0) {
            return false;
        }
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> nums(n);
    for (auto &x : nums) {
        cin >> x;
    }
    int prime_count = 0;
    long long prime_sum = 0;
    for (const auto &x : nums) {
        if (!is_prime_value(x)) {
            continue;
        }
        ++prime_count;
        prime_sum += x;
    }
    cout << prime_count << ' ' << prime_sum << '\n';
    return 0;
}
