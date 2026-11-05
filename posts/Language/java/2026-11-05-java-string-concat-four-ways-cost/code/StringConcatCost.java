import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;
import java.util.stream.Collectors;

/**
 * 같은 조각 N개를 이어 붙이는 네 가지 방법의 시간과 할당량을 잰다.
 *
 * <p>할당량은 현재 스레드가 지금까지 할당한 바이트 수의 차이로 센다.
 * GC 가 언제 돌든 이 값은 바뀌지 않으므로 시간보다 흔들림이 훨씬 적다.
 */
public class StringConcatCost {

  private static final int[] PIECE_COUNTS = {1_000, 10_000, 30_000};
  private static final int ROUNDS = 5;
  private static final com.sun.management.ThreadMXBean THREAD_BEAN =
      (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();

  /** 루프 안에서 += 로 이어 붙인다. 매 회차 새 문자열이 만들어진다. */
  static String loopPlus(String[] pieces) {
    String result = "";
    for (String piece : pieces) {
      result += piece;
    }
    return result;
  }

  /** 루프 밖에서 StringBuilder 하나를 만들고 append 한다. */
  static String builder(String[] pieces) {
    StringBuilder sb = new StringBuilder();
    for (String piece : pieces) {
      sb.append(piece);
    }
    return sb.toString();
  }

  /** String.join (JDK 8 부터). 내부에서 필요한 크기를 한 번에 계산한다. */
  static String join(String[] pieces) {
    return String.join("", pieces);
  }

  /** Stream 으로 모은다. 요소마다 컬렉터가 StringBuilder 하나에 누적한다. */
  static String streamCollect(String[] pieces) {
    return java.util.Arrays.stream(pieces).collect(Collectors.joining());
  }

  /** 한 식 안의 + 는 javac 가 StringBuilder 하나로 바꾼다. javap 로 확인한다. */
  static String singleExpression(String a, String b, String c) {
    return a + b + c;
  }

  /** 컴파일 시점에 값이 정해지는 + 는 javac 가 미리 합친다. */
  static String constantFolding() {
    return "ab" + "cd" + "ef";
  }

  private static String[] makePieces(int count) {
    String[] pieces = new String[count];
    for (int i = 0; i < count; i++) {
      pieces[i] = "item" + (i % 10) + ",";
    }
    return pieces;
  }

  private static void measure(String label, String[] pieces, Supplier<String> work,
      int expectedLength) {
    for (int i = 0; i < 3; i++) {
      work.get();
    }
    long bestNanos = Long.MAX_VALUE;
    long allocatedBytes = 0;
    for (int round = 0; round < ROUNDS; round++) {
      long allocatedBefore = THREAD_BEAN.getThreadAllocatedBytes(Thread.currentThread().getId());
      long start = System.nanoTime();
      String result = work.get();
      long elapsed = System.nanoTime() - start;
      long allocated =
          THREAD_BEAN.getThreadAllocatedBytes(Thread.currentThread().getId()) - allocatedBefore;
      if (result.length() != expectedLength) {
        throw new IllegalStateException(label + " 결과 길이가 다르다: " + result.length());
      }
      if (elapsed < bestNanos) {
        bestNanos = elapsed;
      }
      allocatedBytes = allocated;
    }
    System.out.printf("  %-14s %10.2f ms  %14s KB%n", label, bestNanos / 1e6,
        String.format("%,d", allocatedBytes / 1024));
  }

  public static void main(String[] args) {
    System.out.println("java.version = " + System.getProperty("java.version"));
    System.out.println("java.vm.name = " + System.getProperty("java.vm.name"));
    System.out.println();
    System.out.println("조각은 'item0,' 처럼 6자. 가장 빠른 회차의 시간, 마지막 회차의 할당량.");

    for (int count : PIECE_COUNTS) {
      String[] pieces = makePieces(count);
      int expectedLength = builder(pieces).length();
      System.out.println();
      System.out.printf("[조각 %,d개 -> 결과 %,d자]%n", count, expectedLength);
      System.out.printf("  %-14s %13s  %17s%n", "방법", "시간", "할당량");
      measure("loop +=", pieces, () -> loopPlus(pieces), expectedLength);
      if (args.length > 0 && args[0].equals("plusOnly")) {
        continue;
      }
      measure("StringBuilder", pieces, () -> builder(pieces), expectedLength);
      measure("String.join", pieces, () -> join(pieces), expectedLength);
      measure("stream joining", pieces, () -> streamCollect(pieces), expectedLength);
    }

    if (args.length > 0 && args[0].equals("plusOnly")) {
      return;
    }
    // 같은 입력을 List 로 받는 경우의 join 도 같은 결과인지 확인한다.
    List<String> asList = new ArrayList<>(java.util.Arrays.asList(makePieces(10)));
    System.out.println();
    System.out.println("join(List) 와 join(배열) 결과 동일: "
        + String.join("", asList).equals(join(makePieces(10))));
    System.out.println(singleExpression("a", "b", "c") + " " + constantFolding());
  }
}
