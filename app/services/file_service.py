import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
from app.models.conversion import FileMetadata

logger = logging.getLogger(__name__)


class FileService:
    """파일 관리 서비스"""

    def __init__(self):
        self.upload_dir = Path("./uploads")  # 기본값
        self.temp_dir = Path("./temp")  # 기본값
        self.result_dir = Path("./results")  # 기본값

        # 디렉토리 생성
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)

    async def save_uploaded_file(
        self, file: UploadFile, user_id: Optional[str] = None
    ) -> str:
        """
        업로드된 파일을 저장합니다.

        Args:
            file: 업로드된 파일
            user_id: 사용자 ID

        Returns:
            저장된 파일 경로
        """
        try:
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = file.filename or "unknown"
            safe_filename = f"{timestamp}_{original_name.replace(' ', '_')}"

            # 사용자별 디렉토리 생성
            if user_id:
                user_dir = self.upload_dir / user_id
                user_dir.mkdir(exist_ok=True)
                file_path = user_dir / safe_filename
            else:
                file_path = self.upload_dir / safe_filename

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"파일 저장 완료: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"파일 저장 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")

    async def get_file_metadata(self, file_path: str) -> FileMetadata:
        """
        파일 메타데이터를 조회합니다.

        Args:
            file_path: 파일 경로

        Returns:
            파일 메타데이터
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            stat = path.stat()

            # 파일 타입 확인
            file_type = self._get_file_type(file_path)

            # 페이지 수 추정 (PDF의 경우)
            page_count = None
            if file_type.lower() == "pdf":
                page_count = await self._estimate_pdf_page_count(file_path)

            return FileMetadata(
                file_path=str(file_path),
                file_size=stat.st_size,
                file_type=file_type,
                page_count=page_count,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )

        except Exception as e:
            logger.error(f"파일 메타데이터 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=500, detail="파일 메타데이터 조회에 실패했습니다."
            )

    async def cleanup_temp_files(self, cutoff_time: datetime) -> int:
        """
        임시 파일을 정리합니다.

        Args:
            cutoff_time: 정리 기준 시간

        Returns:
            정리된 파일 수
        """
        try:
            cleaned_count = 0

            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"임시 파일 삭제: {file_path}")
                        except Exception as e:
                            logger.warning(
                                f"임시 파일 삭제 실패: {file_path}, 오류: {str(e)}"
                            )

            logger.info(f"임시 파일 정리 완료: {cleaned_count}개 파일 삭제")
            return cleaned_count

        except Exception as e:
            logger.error(f"임시 파일 정리 실패: {str(e)}")
            raise HTTPException(
                status_code=500, detail="임시 파일 정리에 실패했습니다."
            )

    async def cleanup_old_results(self, cutoff_time: datetime) -> int:
        """
        오래된 결과 파일을 정리합니다.

        Args:
            cutoff_time: 정리 기준 시간

        Returns:
            정리된 파일 수
        """
        try:
            cleaned_count = 0

            for file_path in self.result_dir.rglob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"결과 파일 삭제: {file_path}")
                        except Exception as e:
                            logger.warning(
                                f"결과 파일 삭제 실패: {file_path}, 오류: {str(e)}"
                            )

            logger.info(f"결과 파일 정리 완료: {cleaned_count}개 파일 삭제")
            return cleaned_count

        except Exception as e:
            logger.error(f"결과 파일 정리 실패: {str(e)}")
            raise HTTPException(
                status_code=500, detail="결과 파일 정리에 실패했습니다."
            )

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        저장소 통계 정보를 조회합니다.

        Returns:
            저장소 통계 정보
        """
        try:
            stats = {
                "upload_dir": self._get_dir_stats(self.upload_dir),
                "temp_dir": self._get_dir_stats(self.temp_dir),
                "result_dir": self._get_dir_stats(self.result_dir),
                "total": {"file_count": 0, "total_size": 0},
            }

            # 총계 계산
            for dir_stats in stats.values():
                if isinstance(dir_stats, dict):
                    stats["total"]["file_count"] += dir_stats.get("file_count", 0)
                    stats["total"]["total_size"] += dir_stats.get("total_size", 0)

            return stats

        except Exception as e:
            logger.error(f"저장소 통계 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=500, detail="저장소 통계 조회에 실패했습니다."
            )

    async def move_file_to_result(self, source_path: str, result_filename: str) -> str:
        """
        파일을 결과 디렉토리로 이동합니다.

        Args:
            source_path: 원본 파일 경로
            result_filename: 결과 파일명

        Returns:
            이동된 파일 경로
        """
        try:
            source = Path(source_path)
            destination = self.result_dir / result_filename

            # 파일 이동
            shutil.move(str(source), str(destination))

            logger.info(f"파일 이동 완료: {source} -> {destination}")
            return str(destination)

        except Exception as e:
            logger.error(f"파일 이동 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="파일 이동에 실패했습니다.")

    async def copy_file_to_temp(self, source_path: str) -> str:
        """
        파일을 임시 디렉토리로 복사합니다.

        Args:
            source_path: 원본 파일 경로

        Returns:
            복사된 파일 경로
        """
        try:
            source = Path(source_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"temp_{timestamp}_{source.name}"
            destination = self.temp_dir / temp_filename

            # 파일 복사
            shutil.copy2(str(source), str(destination))

            logger.info(f"파일 복사 완료: {source} -> {destination}")
            return str(destination)

        except Exception as e:
            logger.error(f"파일 복사 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="파일 복사에 실패했습니다.")

    def _get_file_type(self, file_path: str) -> str:
        """파일 타입을 추출합니다."""
        return Path(file_path).suffix.lower().lstrip(".")

    async def _estimate_pdf_page_count(self, file_path: str) -> int:
        """PDF 파일의 페이지 수를 추정합니다."""
        try:
            try:
                from pypdf import PdfReader
            except ImportError:
                logger.warning(
                    "pypdf 패키지가 설치되어 있지 않아 페이지 수를 추정할 수 없습니다."
                )
                return 0

            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                return len(pdf_reader.pages)

        except Exception as e:
            logger.warning(f"PDF 페이지 수 추정 실패: {file_path}, 오류: {str(e)}")
            return 0

    def _get_dir_stats(self, directory: Path) -> Dict[str, Any]:
        """디렉토리 통계를 계산합니다."""
        try:
            file_count = 0
            total_size = 0

            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size

            return {
                "file_count": file_count,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"디렉토리 통계 계산 실패: {directory}, 오류: {str(e)}")
            return {"file_count": 0, "total_size": 0, "total_size_mb": 0}

    async def validate_file_size(
        self, file_path: str, max_size_mb: int = 50
    ) -> bool:  # 기본값 50MB
        """
        파일 크기를 검증합니다.

        Args:
            file_path: 파일 경로
            max_size_mb: 최대 파일 크기 (MB)

        Returns:
            검증 결과
        """
        try:
            file_size = Path(file_path).stat().st_size
            max_size_bytes = max_size_mb * 1024 * 1024

            if file_size > max_size_bytes:
                raise ValueError(
                    f"파일 크기가 최대 크기를 초과했습니다: {file_size / (1024 * 1024):.2f}MB > {max_size_mb}MB"
                )

            return True

        except ValueError as e:
            logger.warning(f"파일 크기 검증 실패: {file_path}, 오류: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"파일 크기 검증 중 오류 발생: {str(e)}")
            raise HTTPException(
                status_code=500, detail="파일 크기 검증에 실패했습니다."
            )

    async def validate_file_type(
        self, file_path: str, allowed_types: Optional[List[str]] = None
    ) -> bool:
        """
        파일 타입을 검증합니다.

        Args:
            file_path: 파일 경로
            allowed_types: 허용된 파일 타입 목록

        Returns:
            검증 결과
        """
        try:
            if allowed_types is None:
                allowed_types = ["pdf"]  # 기본값 PDF만 허용

            file_type = self._get_file_type(file_path)

            if file_type not in allowed_types:
                raise ValueError(f"허용되지 않는 파일 타입입니다: {file_type}")

            return True

        except ValueError as e:
            logger.warning(f"파일 타입 검증 실패: {file_path}, 오류: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"파일 타입 검증 중 오류 발생: {str(e)}")
            raise HTTPException(
                status_code=500, detail="파일 타입 검증에 실패했습니다."
            )
