// 메인 모듈에서 setTimeout 0 과 setImmediate 중 무엇이 먼저 도는지를 자식 프로세스 30개로 센다.
'use strict';

const { spawnSync } = require('node:child_process');

const RUNS = 30;
const CHILD_SOURCE = `
  const order = [];
  setTimeout(() => order.push('timeout'), 0);
  setImmediate(() => order.push('immediate'));
  setTimeout(() => console.log(order.join(',')), 30);
`;

const counts = new Map();
for (let i = 0; i < RUNS; i += 1) {
  const result = spawnSync(process.execPath, ['-e', CHILD_SOURCE], { encoding: 'utf8' });
  const key = result.stdout.trim();
  counts.set(key, (counts.get(key) ?? 0) + 1);
}

console.log(`Node.js ${process.version}, 자식 프로세스 ${RUNS}회`);
for (const [order, count] of counts) console.log(`  ${order} : ${count}회`);
