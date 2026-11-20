#include <iostream>
#include <vector>
using namespace std;

// checks primality
bool check(long v) {
    if (v < 2) return false;
    long d = 2;
    while (d * d <= v) {
        if (v % d == 0) return false;
        d++;
    }
    return true;
}

int main() {
    int len;
    cin >> len;
    vector<int> arr(len);
    for (int k = 0; k < len; k++) cin >> arr[k];
    int cnt = 0;
    long long sum = 0;
    for (int e : arr) {
        if (check(e)) {
            cnt++;
            sum += e;
        }
    }
    cout << cnt << " " << sum << endl;
    return 0;
}
