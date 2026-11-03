import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Locale;

/**
 * 해시가 전부 같은 키를 HashMap 한 버킷에 몰아넣고, 트리화 전후의 조회 시간을 잰다.
 *
 * Java 8 (1.8.0_491) 에서 돌렸다. 외부 의존성은 없다.
 * 버킷의 노드 종류는 리플렉션으로 HashMap.table 을 열어 확인한다.
 */
public final class HashMapTreeify {

    /** hashCode 가 항상 같고 Comparable 이 아니다 — 트리 안에서 순서를 정할 수 없다. */
    static final class PlainKey {
        final int id;

        PlainKey(int id) {
            this.id = id;
        }

        @Override
        public int hashCode() {
            return 1;
        }

        @Override
        public boolean equals(Object other) {
            return other instanceof PlainKey && ((PlainKey) other).id == id;
        }
    }

    /** hashCode 는 같지만 Comparable 이라 트리가 compareTo 로 갈 수 있다. */
    static final class SortableKey implements Comparable<SortableKey> {
        final int id;

        SortableKey(int id) {
            this.id = id;
        }

        @Override
        public int hashCode() {
            return 1;
        }

        @Override
        public boolean equals(Object other) {
            return other instanceof SortableKey && ((SortableKey) other).id == id;
        }

        @Override
        public int compareTo(SortableKey other) {
            return Integer.compare(id, other.id);
        }
    }

    private static final int LOOKUP_ROUNDS = 10;

    /** HashMap.table[bucket] 에 들어 있는 노드 클래스 이름. 비어 있으면 "(비어 있음)". */
    static String bucketNodeType(HashMap<?, ?> map) throws ReflectiveOperationException {
        Field tableField = HashMap.class.getDeclaredField("table");
        tableField.setAccessible(true);
        Object[] table = (Object[]) tableField.get(map);
        if (table == null) {
            return "(table 없음)";
        }
        // hash(key) = h ^ (h >>> 16) = 1, 버킷 = (n - 1) & 1 = 1
        Object node = table[(table.length - 1) & 1];
        return node == null ? "(비어 있음)" : node.getClass().getSimpleName()
            + " (table.length=" + table.length + ")";
    }

    static void section(String title) {
        System.out.println();
        System.out.println("==============================================================");
        System.out.println(title);
        System.out.println("==============================================================");
    }

    /** 키 n 개를 넣고 전부 한 번씩 찾는 데 걸린 평균 시간(µs). */
    static double lookupMicros(HashMap<Object, Integer> map, Object[] keys) {
        long best = Long.MAX_VALUE;
        for (int round = 0; round < LOOKUP_ROUNDS; round++) {
            long started = System.nanoTime();
            int hit = 0;
            for (Object key : keys) {
                if (map.get(key) != null) {
                    hit++;
                }
            }
            long elapsed = System.nanoTime() - started;
            if (hit != keys.length) {
                throw new IllegalStateException("조회 실패: " + hit);
            }
            best = Math.min(best, elapsed);
        }
        return best / 1000.0;
    }

    static Object[] makeKeys(boolean sortable, int count) {
        Object[] keys = new Object[count];
        for (int i = 0; i < count; i++) {
            keys[i] = sortable ? new SortableKey(i) : new PlainKey(i);
        }
        return keys;
    }

    public static void main(String[] args) throws ReflectiveOperationException {
        System.out.println("java.version = " + System.getProperty("java.version"));
        System.out.println("java.vm.name = " + System.getProperty("java.vm.name")
            + " " + System.getProperty("java.vm.version"));

        section("1. 한 버킷에 키를 하나씩 더하며 노드 종류를 본다 (기본 용량 16)");
        HashMap<Object, Integer> small = new HashMap<>();
        for (int i = 1; i <= 12; i++) {
            small.put(new PlainKey(i), i);
            System.out.printf(Locale.ROOT, "  키 %2d개  %s%n", i, bucketNodeType(small));
        }

        section("2. 같은 일을 용량 64 로 시작하면");
        HashMap<Object, Integer> wide = new HashMap<>(64);
        for (int i = 1; i <= 12; i++) {
            wide.put(new PlainKey(i), i);
            System.out.printf(Locale.ROOT, "  키 %2d개  %s%n", i, bucketNodeType(wide));
        }

        section("3. 트리가 됐을 때 조회 시간 — Comparable 여부로 갈린다");
        System.out.println("  키 수     PlainKey(비교 불가)   SortableKey(Comparable)   노드 종류");
        for (int count : new int[] {8, 64, 512, 4096, 16384}) {
            double[] micros = new double[2];
            String nodeType = "";
            for (int variant = 0; variant < 2; variant++) {
                Object[] keys = makeKeys(variant == 1, count);
                HashMap<Object, Integer> map = new HashMap<>();
                for (int i = 0; i < count; i++) {
                    map.put(keys[i], i);
                }
                micros[variant] = lookupMicros(map, keys);
                nodeType = bucketNodeType(map);
            }
            System.out.printf(Locale.ROOT, "  %6d   %14.1f µs   %17.1f µs   %s%n",
                count, micros[0], micros[1], nodeType);
        }

        section("4. 해시가 제대로 퍼지면 트리는 등장하지 않는다 (Integer 키 32768개)");
        HashMap<Object, Integer> spread = new HashMap<>();
        Object[] intKeys = new Object[32768];
        for (int i = 0; i < intKeys.length; i++) {
            intKeys[i] = i * 7919;
            spread.put(intKeys[i], i);
        }
        Field tableField = HashMap.class.getDeclaredField("table");
        tableField.setAccessible(true);
        Object[] table = (Object[]) tableField.get(spread);
        int longest = 0;
        int treeBins = 0;
        Field nextField = Class.forName("java.util.HashMap$Node").getDeclaredField("next");
        nextField.setAccessible(true);
        for (Object head : table) {
            if (head == null) {
                continue;
            }
            if (head.getClass().getSimpleName().equals("TreeNode")) {
                treeBins++;
            }
            int length = 0;
            for (Object node = head; node != null; node = nextField.get(node)) {
                length++;
            }
            longest = Math.max(longest, length);
        }
        System.out.printf(Locale.ROOT, "  table.length=%d  가장 긴 버킷=%d  TreeNode 버킷=%d  조회 %.1f µs%n",
            table.length, longest, treeBins, lookupMicros(spread, intKeys));
    }
}
