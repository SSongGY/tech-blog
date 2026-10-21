/**
 * GC 로그를 만들어 내기 위한 부하다. 두 가지 할당을 섞는다.
 *
 *   - 금방 버려지는 객체: 루프 안에서 만들고 참조를 놓는다. Young 영역에서 끝난다
 *   - 오래 사는 객체: 리스트에 쌓아 두고 일부만 교체한다. Old 영역으로 넘어간다
 *
 * 난수를 쓰지 않으므로 몇 번을 돌려도 같은 양을 할당한다. GC 가 몇 번 일어나는지는
 * 힙 설정에 달려 있고, 그걸 로그로 확인하는 것이 이 예제의 목적이다.
 */
public class AllocationChurn {

    /** 금방 버려지는 배열 한 개의 크기. 바이트. */
    private static final int CHURN_BLOCK_BYTES = 64 * 1024;

    /** 오래 사는 배열 한 개의 크기. 바이트. */
    private static final int RETAINED_BLOCK_BYTES = 256 * 1024;

    /** 오래 사는 배열을 몇 개까지 들고 있을지. 이 수 × 위 크기가 상주 메모리다. */
    private static final int RETAINED_SLOTS = 400;

    /** 버리는 할당을 몇 번 돌릴지. */
    private static final int CHURN_ROUNDS = 240_000;

    /** 몇 번에 한 번씩 오래 사는 배열을 하나 교체할지. */
    private static final int RETAIN_EVERY = 300;

    public static void main(String[] args) {
        byte[][] retained = new byte[RETAINED_SLOTS][];
        long churnedBytes = 0;
        long retainedBytes = 0;
        long checksum = 0;

        long startedAt = System.nanoTime();
        for (int round = 0; round < CHURN_ROUNDS; round++) {
            byte[] block = new byte[CHURN_BLOCK_BYTES];
            // 할당만 하고 안 쓰면 JIT 가 통째로 걷어낼 수 있다. 한 바이트를 만져 둔다.
            block[round % CHURN_BLOCK_BYTES] = (byte) round;
            checksum += block[round % CHURN_BLOCK_BYTES];
            churnedBytes += CHURN_BLOCK_BYTES;

            if (round % RETAIN_EVERY == 0) {
                int slot = (round / RETAIN_EVERY) % RETAINED_SLOTS;
                retained[slot] = new byte[RETAINED_BLOCK_BYTES];
                retained[slot][0] = (byte) slot;
                retainedBytes += RETAINED_BLOCK_BYTES;
            }
        }
        long elapsedNanos = System.nanoTime() - startedAt;

        long liveBytes = 0;
        for (byte[] block : retained) {
            if (block != null) {
                liveBytes += block.length;
            }
        }

        System.out.printf("경과 시간          : %.3f 초%n", elapsedNanos / 1e9);
        System.out.printf("버린 할당          : %,d 바이트 (%.1f MiB)%n",
                churnedBytes, churnedBytes / 1024.0 / 1024.0);
        System.out.printf("오래 사는 할당     : %,d 바이트 (%.1f MiB)%n",
                retainedBytes, retainedBytes / 1024.0 / 1024.0);
        System.out.printf("끝까지 살아남은 양 : %,d 바이트 (%.1f MiB)%n",
                liveBytes, liveBytes / 1024.0 / 1024.0);
        System.out.printf("체크섬             : %d%n", checksum);
    }
}
