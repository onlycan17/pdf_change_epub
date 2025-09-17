"""최소 동작 검증을 위한 스모크 테스트(설명: 시스템이 기본적으로 동작하는지 빠르게 확인하는 검사)."""

from app.main import run


def test_run_does_not_raise() -> None:
    """`run` 함수가 호출되었을 때 예외가 발생하지 않는지 확인합니다."""
    run()
