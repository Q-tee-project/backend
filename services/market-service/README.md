# Market Service

학생-교사 교육 플랫폼의 워크시트 마켓플레이스를 담당하는 마이크로서비스입니다.

## 시스템 개요

Market Service는 교사가 생성한 워크시트를 마켓플레이스에 판매하고, 다른 교사들이 포인트로 구매할 수 있는 기능을 제공합니다.

### 주요 기능

#### 1. 상품 관리 (Product Management)
- **상품 등록**: 국/영/수 워크시트를 마켓에 등록 (자동 가격 책정)
- **상품 조회**: 검색, 필터링, 정렬 지원 (과목, 제목, 태그, 작성자)
- **상품 수정**: 제목 및 설명 수정 (가격/메타데이터는 고정)
- **상품 삭제**: 구매 기록이 없는 상품만 삭제 가능
- **내 상품 목록**: 판매자별 등록 상품 조회

#### 2. 포인트 시스템 (Point System)
- **포인트 충전**: 1,000P 단위로 충전
- **포인트 조회**: 잔액, 총 수익, 총 지출, 총 충전액 확인
- **거래 내역**: 충전, 구매, 판매 수익 내역 조회
- **수수료**: 플랫폼 수수료 10% (판매자는 90% 수익)

#### 3. 구매 시스템 (Purchase System)
- **포인트 구매**: 상품 구매 시 워크시트 자동 복사
- **중복 방지**: 자기 상품, 이미 구매한 상품 구매 차단
- **구매 내역**: 구매 목록 및 구매한 워크시트 조회
- **워크시트 접근**: 구매한 워크시트는 해당 서비스에서 접근

#### 4. 리뷰 시스템 (Review System)
- **리뷰 작성**: 구매자만 평가 가능 (추천/보통/비추천)
- **중복 방지**: 상품당 1회만 리뷰 작성 가능
- **리뷰 조회**: 상품별 리뷰 목록 및 통계
- **만족도 계산**: 추천 비율 자동 계산

### 데이터 모델

#### Product Model
- **MarketProduct**: 상품 정보 (title, price, seller_id, worksheet_data, metadata, stats)
  - 자동 가격 책정: 10문제=1,500P, 20문제=3,000P
  - 워크시트 복사본 저장 (등록 시점 스냅샷)
  - 메타데이터: 학교급, 학년, 과목, 학기, 단원, 태그

#### Purchase Model
- **MarketPurchase**: 구매 기록 (product_id, buyer_id, purchase_price, copied_worksheet_id)
  - 결제 방식: 포인트만 지원
  - 복사된 워크시트 ID 저장

#### Review Model
- **MarketReview**: 리뷰 정보 (product_id, reviewer_id, rating)
  - 평가: recommend/normal/not-recommend
  - 텍스트 리뷰 없음 (간단한 평가만)

#### Point Models
- **UserPoint**: 사용자 포인트 (user_id, available_points, total_earned, total_spent, total_charged)
- **PointTransaction**: 거래 내역 (user_id, transaction_type, amount, balance_after)

### API 엔드포인트

#### Products (`/market/products`)
```
GET    /products                      # 상품 목록 (검색, 필터, 정렬)
GET    /products/{product_id}         # 상품 상세 조회
POST   /products                      # 상품 등록 (교사만)
GET    /my-products                   # 내 상품 목록 (교사만)
PATCH  /products/{product_id}         # 상품 수정 (교사만)
DELETE /products/{product_id}         # 상품 삭제 (교사만)
```

#### Points (`/market/points`)
```
GET    /balance                       # 포인트 잔액 조회
POST   /charge                        # 포인트 충전
GET    /transactions                  # 거래 내역 조회
```

#### Purchase (`/market`)
```
POST   /purchase                           # 포인트로 상품 구매
GET    /my-purchases                       # 내 구매 목록
GET    /purchased/{purchase_id}/worksheet  # 구매한 워크시트 조회
```

#### Reviews (`/market/products/{product_id}/reviews`)
```
POST   /products/{product_id}/reviews        # 리뷰 작성 (구매자만)
GET    /products/{product_id}/reviews        # 리뷰 목록
GET    /products/{product_id}/reviews/stats  # 리뷰 통계
```

### 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (market_service schema)
- **ORM**: SQLAlchemy
- **Authentication**: Auth Service 미들웨어 (JWT 검증)
- **Cache**: Redis
- **HTTP Client**: httpx (비동기)

### 비즈니스 로직

#### 상품 등록 프로세스
1. 워크시트 소유권 확인 (해당 서비스에서 검증)
2. 중복 상품 확인 (같은 워크시트 재등록 방지)
3. 구매한 워크시트 재등록 방지
4. 워크시트 정보 가져오기 (문제 수, 메타데이터)
5. 자동 가격 책정 및 태그 생성
6. 상품 생성

#### 구매 프로세스
1. 상품 정보 확인
2. 자기 상품 구매 방지
3. 중복 구매 확인
4. 구매자 포인트 차감
5. 판매자 포인트 적립 (수수료 10% 제외)
6. 워크시트를 구매자 계정으로 복사
7. 구매 기록 생성
8. 상품 통계 업데이트 (구매 수, 총 매출)

#### 리뷰 프로세스
1. 구매 여부 확인
2. 중복 리뷰 확인
3. 리뷰 생성
4. 상품 통계 업데이트 (리뷰 수, 만족도)

### 외부 서비스 연동

- **Korean Service**: 국어 워크시트 정보 조회, 복사
- **Math Service**: 수학 워크시트 정보 조회, 복사
- **English Service**: 영어 워크시트 정보 조회, 복사
- **Auth Service**: 토큰 검증 (미들웨어)

### 검증 규칙

- 워크시트 소유자만 상품 등록 가능
- 같은 워크시트 중복 등록 불가
- 구매한 워크시트 재등록 불가
- 자기 상품 구매 불가
- 같은 상품 중복 구매 불가
- 구매한 상품만 리뷰 작성 가능
- 상품당 1회만 리뷰 작성 가능
- 구매 기록이 있는 상품은 삭제 불가

### 환경 변수

```bash
DATABASE_URL=postgresql://user:password@postgres:5432/qt_project_db
REDIS_URL=redis://redis:6379/0
KOREAN_SERVICE_URL=http://korean-service:8000
MATH_SERVICE_URL=http://math-service:8000
ENGLISH_SERVICE_URL=http://english-service:8000
AUTH_SERVICE_URL=http://auth-service:8000
PORT=8000
```

### 실행 방법

```bash
# Docker Compose로 실행
docker-compose up market-service

# 개발 모드 (로컬)
cd backend/services/market-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 포트

- **서비스 포트**: 8005 (외부) → 8000 (내부)

### 의존 서비스

- PostgreSQL (데이터베이스)
- Redis (캐싱)
- Auth Service (인증)
- Korean Service (국어 워크시트)
- Math Service (수학 워크시트)
- English Service (영어 워크시트)
