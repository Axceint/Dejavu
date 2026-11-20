import sys

arr = [int(x) for x in sys.stdin.read().split()]
limit = max(arr) if arr else 0
sieve = [True] * (limit + 1)
sieve[0:2] = [False, False][: limit + 1]
for p in range(2, int(limit ** 0.5) + 1):
    if sieve[p]:
        sieve[p * p :: p] = [False] * len(sieve[p * p :: p])
primes = [x for x in arr if x >= 0 and sieve[x]]
print(len(primes), sum(primes))
