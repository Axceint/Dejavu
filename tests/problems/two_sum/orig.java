import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        long k = sc.nextLong();
        HashMap<Long, Long> seen = new HashMap<>();
        long pairs = 0;
        for (int i = 0; i < n; i++) {
            long x = sc.nextLong();
            pairs += seen.getOrDefault(k - x, 0L);
            seen.put(x, seen.getOrDefault(x, 0L) + 1);
        }
        System.out.println(pairs);
    }
}
