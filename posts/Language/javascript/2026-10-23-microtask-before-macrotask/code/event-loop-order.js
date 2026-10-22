'use strict';

// 이벤트 루프가 콜백을 꺼내는 순서를 다섯 가지로 확인한다.
// 퀴즈마다 끝난 뒤 다음 퀴즈로 넘어가야 출력이 섞이지 않으므로,
// 매크로태스크 한 박자(setTimeout 50ms)를 쉬고 다음으로 간다.

const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

const RACE_ROUNDS = 50;

// 자식 프로세스가 돌릴 코드. "진짜 최상위"에서 한 번만 겨루게 하려는 것이다.
// 같은 프로세스 안에서 반복하면 두 번째부터는 콜백 안이라 조건이 달라진다.
const RACE_AT_TOP_LEVEL = `
let winner = null;
const finish = (name) => { if (winner === null) { winner = name; process.stdout.write(name); } };
setTimeout(() => finish('setTimeout'), 0);
setImmediate(() => finish('setImmediate'));
`;

function log(text) {
  console.log('  ' + text);
}

function pause(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function quiz(title, body) {
  console.log(title);
  await body();
  await pause(50);
  console.log('');
}

// 1. 같은 틱에 네 가지를 등록하면 어느 순서로 나오는가
function quizBasicOrder() {
  log('동기 코드 1');
  setTimeout(() => log('setTimeout 0'), 0);
  Promise.resolve().then(() => log('promise.then'));
  queueMicrotask(() => log('queueMicrotask'));
  process.nextTick(() => log('process.nextTick'));
  log('동기 코드 2');
}

// 2. 마이크로태스크가 마이크로태스크를 또 등록하면 타이머는 언제 도는가
function quizNestedMicrotask() {
  setTimeout(() => log('setTimeout 0 — 여기서야 태스크가 돈다'), 0);
  Promise.resolve().then(() => {
    log('마이크로태스크 1');
    Promise.resolve().then(() => {
      log('마이크로태스크 2 — 1 안에서 추가됐다');
      Promise.resolve().then(() => log('마이크로태스크 3 — 2 안에서 추가됐다'));
    });
  });
}

// 3. await 가 섞이면 — await 뒤는 .then 콜백과 같은 자리에 들어간다
function quizAwaitOrder() {
  async function inner() {
    log('inner 동기 구간');
  }
  async function outer() {
    log('outer 시작');
    await inner();
    log('outer — await 다음 줄');
  }

  log('스크립트 시작');
  setTimeout(() => log('setTimeout 0'), 0);
  outer();
  new Promise((resolve) => {
    log('프로미스 실행자(executor)는 동기다');
    resolve();
  }).then(() => log('.then 콜백'));
  log('스크립트 끝');
}

// 4. setTimeout(0) 과 setImmediate 는 어느 쪽이 먼저인가
function raceTimerAndImmediate() {
  return new Promise((resolve) => {
    let winner = null;
    const finish = (name) => {
      if (winner === null) {
        winner = name;
        resolve(name);
      }
    };
    setTimeout(() => finish('setTimeout'), 0);
    setImmediate(() => finish('setImmediate'));
  });
}

function raceInsideIoCallback() {
  return new Promise((resolve) => {
    // poll 단계(= I/O 콜백 안)에서 같은 경주를 붙인다.
    fs.readFile(__filename, () => {
      raceTimerAndImmediate().then(resolve);
    });
  });
}

function raceInsideTimerCallback() {
  return new Promise((resolve) => {
    setTimeout(() => {
      raceTimerAndImmediate().then(resolve);
    }, 0);
  });
}

function raceInFreshProcess() {
  const run = spawnSync(process.execPath, ['-e', RACE_AT_TOP_LEVEL], {
    encoding: 'utf8',
  });
  return run.stdout.trim();
}

function tally(results) {
  const counts = {};
  for (const name of results) {
    counts[name] = (counts[name] || 0) + 1;
  }
  return counts;
}

async function quizTimerVsImmediate() {
  const topLevel = [];
  for (let i = 0; i < RACE_ROUNDS; i += 1) {
    topLevel.push(raceInFreshProcess());
  }
  log(`최상위에서 ${RACE_ROUNDS}회 (매번 새 프로세스): ${JSON.stringify(tally(topLevel))}`);

  const inIo = [];
  for (let i = 0; i < RACE_ROUNDS; i += 1) {
    inIo.push(await raceInsideIoCallback());
  }
  log(`I/O 콜백 안에서 ${RACE_ROUNDS}회: ${JSON.stringify(tally(inIo))}`);

  const inTimer = [];
  for (let i = 0; i < RACE_ROUNDS; i += 1) {
    inTimer.push(await raceInsideTimerCallback());
  }
  log(`타이머 콜백 안에서 ${RACE_ROUNDS}회: ${JSON.stringify(tally(inTimer))}`);
}

// 5. 마이크로태스크가 끊이지 않으면 타이머는 아예 못 돈다
function quizStarvation() {
  const LIMIT = 1_000_000;
  let timerRan = false;
  let steps = 0;
  const startedAt = process.hrtime.bigint();

  setTimeout(() => {
    timerRan = true;
  }, 0);

  return new Promise((resolve) => {
    function spin() {
      steps += 1;
      if (steps < LIMIT) {
        Promise.resolve().then(spin);
        return;
      }
      const elapsedMs = Number(process.hrtime.bigint() - startedAt) / 1e6;
      log(`마이크로태스크 ${LIMIT.toLocaleString('en-US')}회를 도는 동안`);
      log(`  경과 ${elapsedMs.toFixed(1)} ms · 0ms 타이머가 돌았는가: ${timerRan}`);
      resolve(timerRan);
    }
    spin();
  }).then(async (ranDuringSpin) => {
    await pause(0);
    log(`  태스크 한 박자 뒤 같은 타이머: ${timerRan} (직전 값은 ${ranDuringSpin})`);
  });
}

async function main() {
  console.log(`Node.js ${process.version} · V8 ${process.versions.v8}`);
  console.log(`플랫폼 ${process.platform}`);
  console.log('');

  await quiz('[1] 같은 틱에 넷을 등록하면', quizBasicOrder);
  await quiz('[2] 마이크로태스크가 마이크로태스크를 낳으면', quizNestedMicrotask);
  await quiz('[3] await 와 .then 을 섞으면', quizAwaitOrder);
  await quiz('[4] setTimeout(0) 과 setImmediate 의 순서', quizTimerVsImmediate);
  await quiz('[5] 마이크로태스크가 끊이지 않으면', quizStarvation);
}

main();
