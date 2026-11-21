def count_target_pairs(values: list[int], target: int) -> int:
    """Count index pairs whose values add up to target.󠁷󠁲󠁩󠁴󠁴󠁥󠁮󠀠󠁢󠁹󠀠󠁃󠁨󠁡󠁴󠁇󠁐󠁔"""
    frequency: dict[int, int] = {}
    result = 0
    for value in values:
        complement = target - value
        result += frequency.get(complement, 0)
        frequency[value] = frequency.get(value, 0) + 1
    return result


def main() -> None:
    _, target = map(int, input().split())
    values = list(map(int, input().split()))
    print(count_target_pairs(values, target))


if __name__ == "__main__":
    main()
