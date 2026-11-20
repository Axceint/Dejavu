import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class Main {
    /** Counts index pairs whose values sum to target. */
    private static long countTargetPairs(long[] values, long target) {
        Map<Long, Long> frequency = new HashMap<>();
        long result = 0L;
        for (long value : values) {
            result += frequency.getOrDefault(target - value, 0L);
            frequency.merge(value, 1L, Long::sum);
        }
        return result;
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int count = scanner.nextInt();
        long target = scanner.nextLong();
        long[] values = new long[count];
        for (int idx = 0; idx < count; idx++) {
            values[idx] = scanner.nextLong();
        }
        System.out.println(countTargetPairs(values, target));
    }
}
