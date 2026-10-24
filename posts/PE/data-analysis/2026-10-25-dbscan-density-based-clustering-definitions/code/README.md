# DBSCAN 정의 확인 예제

원 논문(Ester, Kriegel, Sander, Xu. *A Density-Based Algorithm for Discovering
Clusters in Large Spatial Databases with Noise*, KDD-96)의 정의 1~6, 보조정리 2,
4.2절 k-dist 휴리스틱을 20점짜리 2차원 표본에서 그대로 계산한다.
비교용으로 같은 표본에 Lloyd k-means(k=2)를 돌린다.

외부 의존성이 없다. 표준 라이브러리(`math`, `platform`, `sys`)만 쓴다.

## 실행

```bash
python dbscan_demo.py
```
