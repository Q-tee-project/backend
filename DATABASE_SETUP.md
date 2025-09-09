# 데이터베이스 설정 가이드

## 자동 설정 (권장)

Docker Compose를 사용하면 데이터베이스와 스키마가 자동으로 설정됩니다:

```bash
docker-compose up -d
```

## DataGrip 연결 설정

### 1. 로컬 PostgreSQL 중지 (포트 충돌 방지)
```bash
brew services stop postgresql
```

### 2. DataGrip 연결 정보
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `qt_project_db`
- **User**: `root`
- **Password**: `1234`

### 3. 스키마 설정
DataGrip에서:
1. Data Source 우클릭 → **Properties**
2. **Schemas** 탭 클릭
3. **Refresh** 버튼 클릭
4. `math_service`, `english_service` 체크
5. **Apply** → **OK**

## 스키마 구조

### math_service 스키마
- `worksheets` - 문제지 정보
- `problems` - 개별 문제
- `math_problem_generations` - 문제 생성 세션
- `grading_sessions` - 채점 세션
- `problem_grading_results` - 문제별 채점 결과

### english_service 스키마
- `grammar_categories` - 문법 카테고리
- `grammar_topics` - 문법 주제
- `grammar_achievements` - 문법 성취도
- `vocabulary_categories` - 어휘 카테고리
- `words` - 단어
- `reading_types` - 독해 유형
- `text_types` - 텍스트 유형

## 수동 스키마 생성 (필요시)

만약 자동 설정이 작동하지 않는 경우:

```sql
-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS math_service;
CREATE SCHEMA IF NOT EXISTS english_service;

-- 기존 테이블 이동 (테이블이 존재하는 경우)
ALTER TABLE worksheets SET SCHEMA math_service;
ALTER TABLE problems SET SCHEMA math_service;
-- ... (기타 테이블들)
```

## 트러블슈팅

### 1. 스키마가 보이지 않는 경우
- DataGrip에서 **Refresh** 실행
- **Data Source Properties** → **Schemas** 에서 스키마 체크

### 2. 연결이 안 되는 경우
- 로컬 PostgreSQL 서비스가 중지되었는지 확인
- Docker 컨테이너가 실행 중인지 확인: `docker ps`

### 3. 포트 충돌
- 로컬 PostgreSQL: `brew services stop postgresql`
- 또는 Docker 포트 변경: `5433:5432`