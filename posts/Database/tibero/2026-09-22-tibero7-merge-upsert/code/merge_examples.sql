SET LINESIZE 140
SET PAGESIZE 200
SET FEEDBACK ON

PROMPT ===== 0. 예제 객체 생성 =====

CREATE TABLE product_master (
  product_id   NUMBER       PRIMARY KEY,
  product_name VARCHAR2(40) NOT NULL,
  price        NUMBER       NOT NULL,
  stock_qty    NUMBER       NOT NULL
);

CREATE TABLE product_feed (
  product_id   NUMBER,
  product_name VARCHAR2(40),
  price        NUMBER,
  stock_qty    NUMBER
);

INSERT INTO product_feed VALUES (1, '기계식 키보드', 95000, 0);
INSERT INTO product_feed VALUES (2, '무선 마우스', 32000, 7);
INSERT INTO product_feed VALUES (3, '모니터 암', 49000, 30);
INSERT INTO product_feed VALUES (5, 'USB-C 케이블', 9000, 100);
COMMIT;

PROMPT ===== 1. 기본 UPSERT =====
PROMPT -- 초기 상태로 되돌린다

DELETE FROM product_master;
INSERT INTO product_master VALUES (1, '기계식 키보드', 89000, 12);
INSERT INTO product_master VALUES (2, '무선 마우스', 32000, 7);
INSERT INTO product_master VALUES (3, '모니터 암', 54000, 0);
INSERT INTO product_master VALUES (4, '노트북 거치대', 21000, 0);
COMMIT;

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty
 WHEN NOT MATCHED THEN
      INSERT (product_id, product_name, price, stock_qty)
      VALUES (s.product_id, s.product_name, s.price, s.stock_qty);

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 2. WHEN MATCHED 만 쓴다 (신규는 무시) =====

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty;

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 3. WHEN NOT MATCHED 만 쓴다 (기존 행은 건드리지 않는다) =====

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN NOT MATCHED THEN
      INSERT (product_id, product_name, price, stock_qty)
      VALUES (s.product_id, s.product_name, s.price, s.stock_qty);

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 4. UPDATE 에 WHERE 를 달아 값이 바뀐 행만 갱신 =====

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty
      WHERE t.price <> s.price;

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 5. DELETE WHERE - 갱신 뒤 값을 기준으로 지운다 =====
PROMPT -- 1번은 12 -> 0 이 되어 지워지고, 3번은 0 -> 30 이 되어 남는다
PROMPT -- 4번은 재고가 0이지만 피드에 없어 갱신되지 않았으므로 남는다

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty
      DELETE WHERE t.stock_qty = 0
 WHEN NOT MATCHED THEN
      INSERT (product_id, product_name, price, stock_qty)
      VALUES (s.product_id, s.product_name, s.price, s.stock_qty);

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 6. UPDATE WHERE 에 걸러진 행은 DELETE WHERE 도 건너뛴다 =====
PROMPT -- 피드에 4번을 같은 가격, 재고 0으로 넣는다
PROMPT -- UPDATE WHERE 가 4번을 거르므로 재고가 0이어도 지워지지 않는다

INSERT INTO product_feed VALUES (4, '노트북 거치대', 21000, 0);
COMMIT;

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty
      WHERE t.price <> s.price
      DELETE WHERE t.stock_qty = 0;

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 7. ON 절에 쓴 컬럼을 UPDATE 하면 어떻게 되는가 =====

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.product_id = s.product_id + 100;

PROMPT ===== 8. 소스에 같은 키가 두 번 있으면 어떻게 되는가 =====

INSERT INTO product_feed VALUES (2, '무선 마우스 v2', 35000, 3);
COMMIT;

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty;

ROLLBACK;

PROMPT ===== 9. 소스를 서브질의로 묶어 중복을 없애면 통과한다 =====

MERGE INTO product_master t
USING (SELECT product_id,
              MAX(price)     AS price,
              MAX(stock_qty) AS stock_qty
         FROM product_feed
        GROUP BY product_id) s
   ON (t.product_id = s.product_id)
 WHEN MATCHED THEN
      UPDATE SET t.price = s.price, t.stock_qty = s.stock_qty;

SELECT product_id, product_name, price, stock_qty
  FROM product_master
 ORDER BY product_id;
ROLLBACK;

PROMPT ===== 10. 타깃에만 있는 행을 다루는 절이 있는가 =====

MERGE INTO product_master t
USING product_feed s
   ON (t.product_id = s.product_id)
 WHEN NOT MATCHED BY SOURCE THEN
      DELETE;

PROMPT ===== 11. 정리 =====

DROP TABLE product_feed;
DROP TABLE product_master;

SELECT COUNT(*) AS obj_left FROM user_objects;

EXIT
