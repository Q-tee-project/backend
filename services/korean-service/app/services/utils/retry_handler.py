"""재시도 및 예외 처리 유틸리티"""
import time
from typing import Callable, TypeVar, Optional

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    silent: bool = True
) -> Optional[T]:
    """
    함수를 재시도하며 실패 시 백오프

    Args:
        func: 실행할 함수
        max_retries: 최대 재시도 횟수
        backoff_seconds: 재시도 간 대기 시간
        silent: True면 예외를 무시하고 None 반환

    Returns:
        함수 실행 결과 또는 None
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                if silent:
                    return None
                raise
            if backoff_seconds > 0:
                time.sleep(backoff_seconds)
    return None
