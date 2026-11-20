from collections import defaultdict


def count_pairs(arr, k):
    seen = defaultdict(int)
    pairs = 0
    for x in arr:
        pairs += seen[k - x]
        seen[x] += 1
    return pairs


n, k = map(int, input().split())
arr = list(map(int, input().split()))
print(count_pairs(arr, k))
