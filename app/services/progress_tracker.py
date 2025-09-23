"""단계별 진행 상태 추적 서비스

경량 인메모리 트래커로, 변환 파이프라인에서 호출하여 단계 이력(이름, 진행률, 메시지)을
저장하고 조회할 수 있게 합니다. 추후 Redis 등으로 대체하기 쉽도록 단순한 인터페이스를 제공합니다.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List


class ProgressTracker:
    """간단한 인메모리 진행 단계 추적기.

    저장 형태:
      _store: { conversion_id: [ {name, progress, message, ts}, ... ] }
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def set_step(self, conversion_id: str, name: str, progress: int, message: str = "") -> None:
        """단계 추가 또는 갱신

        Args:
            conversion_id: 변환 작업 ID
            name: 단계 이름
            progress: 0-100
            message: 보조 메시지
        """
        async with self._lock:
            lst = self._store.get(conversion_id)
            if lst is None:
                lst = []
                self._store[conversion_id] = lst

            # append step snapshot
            lst.append({"name": name, "progress": int(progress), "message": message})

    async def get_steps(self, conversion_id: str) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self._store.get(conversion_id, []))

    async def clear(self, conversion_id: str) -> None:
        async with self._lock:
            if conversion_id in self._store:
                del self._store[conversion_id]
