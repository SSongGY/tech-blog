// Node.js 이벤트 루프에서 콜백이 실행되는 순서를 네 가지 상황으로 확인한다.
'use strict';

const fs = require('node:fs');

function runTopLevelOrder() {
  // 메인 모듈이 끝난 직후의 순서. setTimeout 대 setImmediate 는 프로세스 상태에 따라 갈릴 수 있어 따로 센다.
  const log = [];
  setTimeout(() => log.push('setTimeout 0'), 0);
  setImmediate(() => log.push('setImmediate'));
  Promise.resolve().then(() => log.push('promise.then'));
  process.nextTick(() => log.push('nextTick'));
  queueMicrotask(() => log.push('queueMicrotask'));
  log.push('동기 코드 끝');
  return log;
}

function runInsideIoCallback() {
  // I/O 콜백 안에서는 poll 단계 직후 check 단계가 오므로 setImmediate 가 항상 먼저다.
  return new Promise((resolve) => {
    fs.readFile(__filename, () => {
      const log = [];
      setTimeout(() => log.push('setTimeout 0'), 0);
      setImmediate(() => log.push('setImmediate'));
      setTimeout(() => resolve(log), 20);
    });
  });
}

function runMicrotaskBetweenTimers() {
  // 같은 timers 단계의 콜백 사이에서도 마이크로태스크가 비워지는지 본다.
  return new Promise((resolve) => {
    const log = [];
    setTimeout(() => {
      log.push('timer A');
      Promise.resolve().then(() => log.push('A 의 promise'));
      process.nextTick(() => log.push('A 의 nextTick'));
    }, 0);
    setTimeout(() => log.push('timer B'), 0);
    setTimeout(() => resolve(log), 20);
  });
}

function runNextTickStarvation() {
  // nextTick 이 자기 자신을 다시 예약하면 setImmediate 가 얼마나 밀리는지 센다.
  return new Promise((resolve) => {
    let ticks = 0;
    const MAX_TICKS = 100000;
    function again() {
      ticks += 1;
      if (ticks < MAX_TICKS) process.nextTick(again);
    }
    let ticksWhenImmediateRan = null;
    setImmediate(() => {
      ticksWhenImmediateRan = ticks;
      resolve({ ticksWhenImmediateRan, MAX_TICKS });
    });
    process.nextTick(again);
  });
}

async function main() {
  console.log(`Node.js ${process.version} / ${process.platform}`);

  const top = runTopLevelOrder();
  await new Promise((r) => setTimeout(r, 50));
  console.log('\n1. 메인 모듈 직후');
  top.forEach((line, i) => console.log(`  ${i + 1}. ${line}`));

  console.log('\n2. fs.readFile 콜백 안');
  (await runInsideIoCallback()).forEach((line, i) => console.log(`  ${i + 1}. ${line}`));

  console.log('\n3. 같은 timers 단계의 두 콜백 사이');
  (await runMicrotaskBetweenTimers()).forEach((line, i) => console.log(`  ${i + 1}. ${line}`));

  const starve = await runNextTickStarvation();
  console.log('\n4. nextTick 연쇄 예약');
  console.log(`  setImmediate 가 실행됐을 때 nextTick 은 ${starve.ticksWhenImmediateRan}번 돈 뒤 (상한 ${starve.MAX_TICKS})`);

  // 1번에서 setTimeout 과 setImmediate 의 순서가 고정인지 별도 프로세스 30개로 센다
  console.log('\n5. 메인 모듈에서 setTimeout 0 대 setImmediate (자식 프로세스 반복)');
  require('./timeout-vs-immediate-repeat.js');
}

main();
