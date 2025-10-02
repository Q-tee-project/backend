# /services/math-service/app/services/ai_client.py

from .problem_generator import ProblemGenerator

# 애플리케이션이 로드될 때 단 한 번만 ProblemGenerator를 생성합니다.
# 이 인스턴스가 모든 Celery task와 서비스에서 공유됩니다.
problem_generator_instance = ProblemGenerator()


