n, k = map(int, input().split())
a = sorted(map(int, input().split()))
lo, hi, ans = 0, n - 1, 0
while lo < hi:
    s = a[lo] + a[hi]
    if s < k:
        lo += 1
    elif s > k:
        hi -= 1
    elif a[lo] == a[hi]:
        m = hi - lo + 1
        ans += m * (m - 1) // 2
        break
    else:
        left, right = 1, 1
        while lo + 1 < hi and a[lo + 1] == a[lo]:
            lo += 1
            left += 1
        while hi - 1 > lo and a[hi - 1] == a[hi]:
            hi -= 1
            right += 1
        ans += left * right
        lo += 1
        hi -= 1
print(ans)
