# 글 목록

총 **54편** · 갱신 2026-09-23

> 이 파일은 `python scripts/blog.py index`가 생성한다. 직접 고치지 말 것.

## DB문법 (basics) — 10편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-23 | [LEFT JOIN — 없는 쪽을 남기는 조인](posts/Database/sql-basics/2026-09-23-left-join-basics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [INNER JOIN — 두 테이블을 잇는 기본](posts/Database/sql-basics/2026-09-23-inner-join-basics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [CROSS JOIN과 SELF JOIN — 언제 쓰는가](posts/Database/sql-basics/2026-09-23-cross-join-and-self-join/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-22 | [LIMIT과 OFFSET — 결과를 잘라내는 문법](posts/Database/sql-basics/2026-09-22-limit-offset-pagination/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [HAVING과 WHERE — 어느 단계에서 걸러지는가](posts/Database/sql-basics/2026-09-22-having-vs-where/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-22 | [GROUP BY와 집계 함수 — 묶는 기준 정하기](posts/Database/sql-basics/2026-09-22-group-by-aggregate-null/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [DISTINCT — 중복 제거가 정렬을 부르는 이유](posts/Database/sql-basics/2026-09-22-distinct-and-sorting/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [WHERE 조건 — AND와 OR의 우선순위](posts/Database/sql-basics/2026-09-21-where-and-or-precedence/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [ORDER BY — 다중 정렬과 NULL이 놓이는 자리](posts/Database/sql-basics/2026-09-21-order-by-null-placement/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [SELECT 기본 — 컬럼 고르기와 별칭](posts/Database/sql-basics/2026-09-18-select-columns-and-aliases/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |

## DB기능 (product) — 5편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-23 | [Tibero 7 분석 함수의 윈도우 절 — ROWS와 RANGE는 어디서 갈리는가](posts/Database/tibero/2026-09-23-tibero7-window-clause/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-23 | [Tibero 7 파티션 테이블 — 종류별로 언제 쓰는가](posts/Database/tibero/2026-09-23-tibero7-partition-table-types/index.md) | 심화 | Tibero 7.2 | 실행 검증 |
| 2026-09-22 | [Tibero 7 MERGE 문 — UPSERT를 한 문장으로, 그리고 DELETE 절의 함정](posts/Database/tibero/2026-09-22-tibero7-merge-upsert/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-22 | [Tibero 7 계층 질의 — CONNECT BY와 순환 참조](posts/Database/tibero/2026-09-22-tibero7-connect-by-hierarchy/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-18 | [Tibero 7 시퀀스 — 생성, 캐시, 그리고 값이 건너뛰는 순간](posts/Database/tibero/2026-09-18-tibero7-sequence-cache/index.md) | 입문 | Tibero 7.2 | 실행 검증 |

## 기술사 (pe) — 21편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-23 | [프로세스 상태 전이 모델 — 5상태와 대기 큐](posts/PE/system/2026-09-23-process-state-transition-model/index.md) | 중급 | Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018), Stallings, Operating Systems: Internals and Design Principles §3.2, IEEE Std 1003.1-2024 (POSIX.1-2024), Linux man-pages — proc_pid_stat(5)·proc_loadavg(5), 2026-09-23 조회 | 문서 근거 |
| 2026-09-23 | [Physical AI — 인지·추론·행동 순환과 시뮬레이션 기반 학습](posts/PE/emerging-tech/2026-09-23-physical-ai-perception-action-loop/index.md) | 중급 | RT-2 arXiv:2307.15818 (2023-07), GR00T N1 arXiv:2503.14734 (2025-03), Tobin et al. arXiv:1703.06907 (2017-03), WEF Physical AI White Paper (2025-09), ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-23 | [정규화 1NF부터 BCNF까지](posts/PE/database/2026-09-23-normalization-1nf-to-bcnf/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Windows 11 | 실행 검증 |
| 2026-09-23 | [분산 데이터베이스 — 투명성 6가지](posts/PE/database/2026-09-23-distributed-database-transparency/index.md) | 심화 | Özsu & Valduriez, IEEE Computer 24(8) 1991, Oracle Database 19c 문서, Oracle Database 11g R2 문서 | 문서 근거 |
| 2026-09-23 | [트랜잭션 ACID와 격리 수준 — 이상현상으로 수준을 정의하는 방식](posts/PE/database/2026-09-23-acid-and-isolation-levels/index.md) | 중급 | PostgreSQL 16 문서, Berenson et al., SIGMOD 1995 | 문서 근거 |
| 2026-09-22 | [SQuaRE 표준군 구조 — 5개 부문과 확장 부문, 그리고 품질 모델 4종](posts/PE/software-engineering/2026-09-22-square-standard-family-structure/index.md) | 중급 | ISO/IEC 25000:2014 (2판), ISO/IEC 25002:2024 (1판), ISO/IEC 25010:2023 (2판), ISO/IEC 25019:2023 (1판) | 문서 근거 |
| 2026-09-22 | [MSA — 분해 기준과 감당해야 할 비용](posts/PE/software-engineering/2026-09-22-msa-decomposition-and-cost/index.md) | 심화 | NIST SP 800-204 (2019-08) | 문서 근거 |
| 2026-09-22 | [형상관리 — 4대 활동과 베이스라인](posts/PE/software-engineering/2026-09-22-configuration-management-baseline/index.md) | 중급 | ISO/IEC TR 19759:2016 (SWEBOK V3.0), ISO/IEC/IEEE 24765:2017, IEEE 828-2012 | 문서 근거 |
| 2026-09-22 | [CMMI 성숙도 레벨과 프랙티스 영역 — 0단계부터 5단계까지](posts/PE/software-engineering/2026-09-22-cmmi-maturity-levels/index.md) | 중급 | CMMI V3.0 (2023), CMMI V2.0 (2018), ISO/IEC 33001:2015, ISO/IEC 33004:2015 | 문서 근거 |
| 2026-09-22 | [부트스트랩 재표집 — 복원추출로 추정량의 분포를 세우는 절차](posts/PE/data-analysis/2026-09-22-bootstrap-resampling/index.md) | 중급 | Python 3.13.5, Efron, Ann. Statist. 7(1), 1979, Efron & Narasimhan, 2018 preprint | 실행 검증 |
| 2026-09-22 | [BM25 — 확률적 적합성 프레임워크가 낳은 순위 함수와 두 매개변수](posts/PE/software-engineering/2026-09-22-bm25-probabilistic-relevance/index.md) | 중급 | Robertson & Zaragoza, FnTIR 3(4), 2009, Apache Lucene 10.3.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [근사 최근접 이웃 탐색과 HNSW 색인 — 정확한 답을 포기하고 얻는 것](posts/PE/database/2026-09-22-approximate-nearest-neighbor-hnsw/index.md) | 중급 | Python 3.13.5, Malkov & Yashunin, arXiv:1603.09320v4 (2018), pgvector 0.8.6 | 실행 검증 |
| 2026-09-22 | [애자일과 DevOps — 무엇이 같고 무엇이 다른가](posts/PE/software-engineering/2026-09-22-agile-and-devops-scope/index.md) | 중급 | ISO/IEC/IEEE 32675:2022, IEEE Std 2675-2021, 애자일 선언문 (2001), Scrum Guide 2020 | 문서 근거 |
| 2026-09-21 | [테스트 레벨과 테스트 기법 분류](posts/PE/software-engineering/2026-09-21-test-levels-and-techniques/index.md) | 중급 | ISTQB CTFL Syllabus v4.0.1 (2024-09-15), Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [품질속성 시나리오와 유틸리티 트리](posts/PE/software-engineering/2026-09-21-quality-attribute-scenario-utility-tree/index.md) | 중급 | CMU/SEI-2000-TR-004 (2000.8), CMU/SEI-2003-TR-016 (2003.8) | 문서 근거 |
| 2026-09-21 | [정보시스템 감리 — 제3자 점검이 법으로 자리 잡은 구조](posts/PE/it-management/2026-09-21-information-system-audit/index.md) | 중급 | 전자정부법 (법률 제21394호, 2026.2.27. 일부개정), 전자정부법 시행령 (대통령령 제36605호, 2026.8.25. 일부개정), 정보시스템 감리기준 (행정안전부고시 제2024-53호, 2024.6.27.) | 문서 근거 |
| 2026-09-21 | [다크 팩토리 — 무인화가 성립하기 위한 전제](posts/PE/emerging-tech/2026-09-21-dark-factory-prerequisites/index.md) | 중급 | acatech Industrie 4.0 Maturity Index (2017, UPDATE 2020), IEC 62264-1:2013, ISO 13374-1:2003, ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-21 | [결합도와 응집도 — 등급별 판별 기준](posts/PE/software-engineering/2026-09-21-coupling-and-cohesion-levels/index.md) | 입문 | ISO/IEC/IEEE 24765:2017, ISO/IEC TR 19759:2016 (SWEBOK V3) | 문서 근거 |
| 2026-09-21 | [업무 프로세스 재설계(BPR) — 원안과 AI 도입 이후](posts/PE/it-management/2026-09-21-bpr-reengineering-and-ai/index.md) | 중급 | Hammer & Champy, Reengineering the Corporation (1993), Process Mining Manifesto (LNBIP 99, 2012), IEEE 1849-2016 (XES), ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023) | 문서 근거 |
| 2026-09-18 | [소프트웨어 아키텍처 4+1 뷰](posts/PE/software-engineering/2026-09-18-software-architecture-4plus1-views/index.md) | 중급 | IEEE Software 12(6) 1995, ISO/IEC/IEEE 42010:2022 | 문서 근거 |
| 2026-09-18 | [요구공학 — 도출부터 검증까지 4단계](posts/PE/software-engineering/2026-09-18-requirements-engineering-four-phases/index.md) | 중급 | SWEBOK Guide V3.0, ISO/IEC/IEEE 29148:2018 | 문서 근거 |

## 리눅스 (linux) — 4편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-23 | [sed — 파일 일괄 치환을 안전하게 하는 법](posts/Linux/command/2026-09-23-sed-safe-bulk-replace/index.md) | 중급 | GNU sed 4.9, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-22 | [grep — 로그에서 원하는 줄만 뽑기](posts/Linux/command/2026-09-22-grep-context-and-pcre/index.md) | 입문 | GNU grep 3.0, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-22 | [awk — 로그를 표로 집계하기](posts/Linux/command/2026-09-22-awk-log-aggregation/index.md) | 중급 | GNU Awk 5.4.0, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-21 | [TLS 핸드셰이크에서 실제로 오가는 것](posts/Infra/tls/2026-09-21-tls-handshake-openssl/index.md) | 중급 | OpenSSL 3.5.6 (2026-04-07), Git Bash on Windows 11, Python 3.13.5 | 실행 검증 |

## 일반 (general) — 4편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-21 | [트랜잭션 격리 수준별로 실제 무슨 이상 현상이 보이는가](posts/Database/sqlite/2026-09-21-isolation-level-anomalies/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [git bisect로 버그가 들어온 커밋을 자동으로 찾기](posts/Tooling/git/2026-09-18-git-bisect-run-automation/index.md) | 중급 | git 2.54.0.windows.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [복합 인덱스의 컬럼 순서가 성능을 가르는 이유](posts/Database/sqlite/2026-09-18-composite-index-column-order/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [B-Tree 인덱스를 못 타는 조건들](posts/Database/sqlite/2026-09-18-btree-index-not-used/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |

## 기출문제 (exam) — 10편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-09-23 | [기출문제 — Physical AI와 생성형 AI 비교](posts/PE/exam/2026-09-23-physical-ai-vs-generative-ai/index.md) | 중급 | NIST AI 600-1 (2024-07), RT-2 arXiv:2307.15818 (2023-07), WEF Physical AI White Paper (2025-09) | 문서 근거 |
| 2026-09-23 | [기출문제 — 차등 맨체스터(Differential Manchester) 부호화](posts/PE/exam/2026-09-23-differential-manchester-encoding/index.md) | 중급 | IEEE 802.5 (Token Ring), IEEE 802.3cg Draft D0.3 (2017-11), Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [기출문제 — 좀비 프로세스](posts/PE/exam/2026-09-22-zombie-process/index.md) | 중급 | IEEE Std 1003.1-2024 (POSIX.1-2024), Linux man-pages — wait(2)·proc(5)·pid_namespaces(7), 2026-09-22 조회, Docker Engine CLI 문서 (docker run --init), 2026-09-22 조회 | 문서 근거 |
| 2026-09-22 | [기출문제 — 잭나이프 기법의 편향 감소와 분산 추정](posts/PE/exam/2026-09-22-jackknife-resampling/index.md) | 중급 | Python 3.13.5, Efron & Stein, Ann. Statist. 9(3), 1981, Shao & Wu, Ann. Statist. 17(3), 1989 | 실행 검증 |
| 2026-09-22 | [기출문제 — ISO/IEC 25010 제품 품질 모델의 주특성과 부특성](posts/PE/exam/2026-09-22-iso-iec-25010-product-quality-model/index.md) | 중급 | ISO/IEC 25010:2023 (2판, 2023-11), ISO/IEC 25010:2011 (1판) | 문서 근거 |
| 2026-09-22 | [기출문제 — 어휘 검색과 의미 검색을 결합한 하이브리드 검색](posts/PE/exam/2026-09-22-hybrid-search-lexical-vector/index.md) | 중급 | Cormack et al., SIGIR 2009 (RRF), Karpukhin et al., EMNLP 2020 (DPR), Bruch et al., ACM TOIS 2023 | 문서 근거 |
| 2026-09-21 | [기출문제 — PMC와 PMO 비교](posts/PE/exam/2026-09-21-pmc-pmo/index.md) | 중급 | 전자정부법 제64조의2, 전자정부사업관리 위탁에 관한 규정 (2024.6.27 일부개정), PMBOK Guide 5th Edition (2013) | 문서 근거 |
| 2026-09-21 | [기출문제 — 다크 팩토리(Dark Factory)](posts/PE/exam/2026-09-21-dark-factory/index.md) | 중급 | IEC 62264-1:2013, ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-21 | [기출문제 — ATAM(Architecture Trade-off Analysis Method)](posts/PE/exam/2026-09-21-atam/index.md) | 중급 | CMU/SEI-2000-TR-004 (2000.8), Evaluating Software Architectures (2002) | 문서 근거 |
| 2026-09-21 | [기출문제 — AI 기반 업무 프로세스 재설계(BPR) 도입 효과](posts/PE/exam/2026-09-21-ai-driven-bpr/index.md) | 중급 | Hammer & Champy, Reengineering the Corporation (1993), IEEE 1849-2023 (XES), ISO/IEC 22989:2022, ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023) | 문서 근거 |

## 같은 기능을 여러 환경에서 다룬 글

**`transaction-isolation`**

- [트랜잭션 격리 수준별로 실제 무슨 이상 현상이 보이는가](posts/Database/sqlite/2026-09-21-isolation-level-anomalies/index.md) — SQLite 3.49.1, Python 3.13.5
- [트랜잭션 ACID와 격리 수준 — 이상현상으로 수준을 정의하는 방식](posts/PE/database/2026-09-23-acid-and-isolation-levels/index.md) — PostgreSQL 16 문서, Berenson et al., SIGMOD 1995

