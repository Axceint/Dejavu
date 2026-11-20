import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.StringTokenizer;

public class Main {
    private static boolean isPrimeNumber(final int value) {
        if (value < 2) {
            return false;
        }
        int divisor = 2;
        while (divisor * divisor <= value) {
            if (value % divisor == 0) {
                return false;
            }
            divisor++;
        }
        return true;
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        int n = Integer.parseInt(reader.readLine().trim());
        StringTokenizer tokens = new StringTokenizer(reader.readLine());
        int primeCount = 0;
        long primeSum = 0L;
        for (int i = 0; i < n; i++) {
            int current = Integer.parseInt(tokens.nextToken());
            if (isPrimeNumber(current)) {
                primeCount++;
                primeSum += current;
            }
        }
        System.out.println(primeCount + " " + primeSum);
    }
}
