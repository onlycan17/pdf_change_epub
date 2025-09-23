"""이미지 최적화 및 WebP 변환 서비스

설명: PDF에서 추출된 원본 이미지를 용량을 줄이면서 품질을 유지하도록
크기 제한 및 WebP 포맷으로 변환합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import io

from PIL import Image


@dataclass
class OptimizedImage:
    """최적화된 이미지 결과"""

    data: bytes
    format: str
    width: int
    height: int
    original_format: Optional[str] = None
    original_size: Optional[int] = None


def _resize_within_bounds(
    image: Image.Image, max_width: int, max_height: int
) -> Tuple[Image.Image, int, int]:
    """이미지를 비율 유지하며 최대 크기 내로 리사이즈"""
    width, height = image.size
    if width <= max_width and height <= max_height:
        return image, width, height

    # 비율 유지 스케일 계산
    width_ratio = max_width / float(width)
    height_ratio = max_height / float(height)
    ratio = min(width_ratio, height_ratio)
    new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
    return image.resize(new_size, Image.LANCZOS), new_size[0], new_size[1]


def optimize_image_to_webp(
    image_bytes: bytes,
    *,
    max_width: int = 1600,
    max_height: int = 1600,
    quality: int = 80,
) -> OptimizedImage:
    """이미지를 WebP로 최적화 변환

    용어(품질: 이미지 압축 정도. 100이 최고 화질/최대 용량, 80은 고화질로 일반적으로 권장)

    Args:
        image_bytes: 원본 이미지 바이트
        max_width: 최대 가로 크기(px)
        max_height: 최대 세로 크기(px)
        quality: WebP 품질(0~100)

    Returns:
        OptimizedImage: 변환된 이미지와 메타정보
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        original_format = (im.format or "").lower() or None

        # 팔레트/모드 정규화 (WebP 호환)
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        elif im.mode == "CMYK":
            im = im.convert("RGB")

        resized, width, height = _resize_within_bounds(im, max_width, max_height)

        out = io.BytesIO()
        # lossless는 용량 증가 가능. 일반적으로 quality 기반 손실압축이 유리
        resized.save(out, format="WEBP", quality=quality, method=6)
        data = out.getvalue()

    return OptimizedImage(
        data=data,
        format="webp",
        width=width,
        height=height,
        original_format=original_format,
        original_size=len(image_bytes),
    )
