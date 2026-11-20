import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer st = new StringTokenizer(br.readLine());
        int n = Integer.parseInt(st.nextToken());
        int k = Integer.parseInt(st.nextToken());
        int[] a = Arrays.stream(br.readLine().trim().split("\\s+")).mapToInt(Integer::parseInt).toArray();
        Arrays.sort(a);
        long c = 0;
        for (int i = 0; i < n; i++) {
            int need = k - a[i];
            c += lowerBound(a, i + 1, need + 1) - lowerBound(a, i + 1, need);
        }
        System.out.println(c);
    }

    static int lowerBound(int[] a, int from, int v) {
        int l = from, r = a.length;
        while (l < r) {
            int m = (l + r) >>> 1;
            if (a[m] < v) l = m + 1; else r = m;
        }
        return l;
    }
}
