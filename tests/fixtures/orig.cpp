#include <iostream>
#include <vector>
using namespace std;

bool isPrime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];
    int count = 0;
    long long total = 0;
    for (int x : a) {
        if (isPrime(x)) {
            count++;
            total += x;
        }
    }
    cout << count << " " << total << endl;
    return 0;
}
