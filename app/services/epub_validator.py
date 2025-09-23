"""EPUB 유효성 검증 서비스

설명: .epub 파일이 기본 EPUB 구조를 만족하는지 경량 검증합니다.

검증 항목(핵심):
- mimetype 첫 항목, 비압축, 내용은 application/epub+zip
- META-INF/container.xml 존재 및 content.opf 경로 가리킴
- content.opf 존재, package 루트/버전/manifest/spine 존재
- EPUB3: nav 문서(properties~="nav") 존재, 파일 존재
- EPUB2: spine@toc가 가리키는 toc.ncx 존재
- manifest 항목 파일들이 ZIP 내부에 실제 존재
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import io
import zipfile
import posixpath
import xml.etree.ElementTree as ET


@dataclass
class EPUBValidationIssue:
    level: str  # "error" | "warning"
    code: str
    message: str
    path: Optional[str] = None


@dataclass
class EPUBValidationResult:
    valid: bool
    errors: List[EPUBValidationIssue] = field(default_factory=list)
    warnings: List[EPUBValidationIssue] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


def validate_epub_bytes(epub_bytes: bytes) -> EPUBValidationResult:
    errors: List[EPUBValidationIssue] = []
    warnings: List[EPUBValidationIssue] = []
    meta: Dict[str, str] = {}

    try:
        zf = zipfile.ZipFile(io.BytesIO(epub_bytes))
    except Exception:
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="ZIP_INVALID",
                message="EPUB은 ZIP 형식이어야 합니다.",
            )
        )
        return EPUBValidationResult(valid=False, errors=errors, warnings=warnings)

    # 1) mimetype 검사: 첫 항목, 비압축, 정확한 내용
    infolist = zf.infolist()
    if not infolist:
        errors.append(
            EPUBValidationIssue(
                level="error", code="ZIP_EMPTY", message="EPUB ZIP이 비어 있습니다."
            )
        )
        return EPUBValidationResult(valid=False, errors=errors, warnings=warnings)

    first = infolist[0]
    try:
        data = zf.read(first)
    except Exception:
        data = b""
    if first.filename != "mimetype":
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="MIMETYPE_FIRST",
                message='첫 ZIP 항목은 "mimetype"여야 합니다.',
                path=first.filename,
            )
        )
    if first.compress_type != zipfile.ZIP_STORED:
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="MIMETYPE_STORED",
                message="mimetype는 비압축으로 저장되어야 합니다.",
                path=first.filename,
            )
        )
    if data != b"application/epub+zip":
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="MIMETYPE_CONTENT",
                message='mimetype 내용은 "application/epub+zip"이어야 합니다.',
                path="mimetype",
            )
        )

    # 2) container.xml 검사
    container_path = "META-INF/container.xml"
    if container_path not in zf.namelist():
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="CONTAINER_MISSING",
                message="META-INF/container.xml 누락",
                path=container_path,
            )
        )
        return EPUBValidationResult(valid=False, errors=errors, warnings=warnings)

    try:
        container_xml = zf.read(container_path)
        ct = ET.fromstring(container_xml)
        ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile = ct.find(".//c:rootfile", ns)
        if rootfile is None:
            raise ValueError("rootfile 요소 없음")
        opf_path = rootfile.get("full-path") or ""
        if not opf_path or opf_path not in zf.namelist():
            raise ValueError("content.opf 경로가 잘못되었거나 파일이 없음")
    except Exception as e:
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="CONTAINER_INVALID",
                message=f"container.xml 파싱 실패: {e}",
                path=container_path,
            )
        )
        return EPUBValidationResult(valid=False, errors=errors, warnings=warnings)

    meta["opf_path"] = opf_path

    # 3) content.opf 검사
    try:
        opf_xml = zf.read(opf_path)
        pkg = ET.fromstring(opf_xml)
        # EPUB 2.0: http://www.idpf.org/2007/opf
        # EPUB 3.x: http://www.idpf.org/2007/opf (동일) 네임스페이스 사용
        ns = {"opf": pkg.tag[pkg.tag.find("{") + 1 : pkg.tag.find("}")]}
        if not pkg.tag.endswith("package"):
            raise ValueError("루트 요소가 package가 아님")
        version = pkg.get("version", "")
        meta["version"] = version

        manifest = pkg.find("opf:manifest", ns)
        spine = pkg.find("opf:spine", ns)
        if manifest is None or spine is None:
            raise ValueError("manifest 또는 spine 누락")

        # manifest 파일 존재 여부 확인
        base_dir = posixpath.dirname(opf_path)
        items = manifest.findall("opf:item", ns)
        hrefs = []
        for it in items:
            href = it.get("href") or ""
            if not href:
                errors.append(
                    EPUBValidationIssue(
                        level="error",
                        code="MANIFEST_ITEM_NO_HREF",
                        message="manifest item에 href 누락",
                        path=opf_path,
                    )
                )
                continue
            joined = posixpath.normpath(posixpath.join(base_dir, href))
            hrefs.append((it, joined))
            if joined not in zf.namelist():
                errors.append(
                    EPUBValidationIssue(
                        level="error",
                        code="RESOURCE_MISSING",
                        message=f"manifest 리소스 누락: {href}",
                        path=joined,
                    )
                )

        # EPUB3: nav 확인
        try:
            ver = float(version) if version else 0.0
        except Exception:
            ver = 0.0

        if ver >= 3.0:
            nav_found = False
            for it, joined in hrefs:
                props = (it.get("properties") or "").lower()
                if "nav" in props:
                    nav_found = True
                    break
            if not nav_found:
                errors.append(
                    EPUBValidationIssue(
                        level="error",
                        code="NAV_MISSING",
                        message="EPUB3에서 nav 문서가 필요합니다.",
                        path=opf_path,
                    )
                )
        else:
            # EPUB2: spine@toc -> toc.ncx 존재 확인
            toc_id = spine.get("toc") if spine is not None else None
            if toc_id:
                # 해당 id의 item 찾기
                found = None
                for it in items:
                    if it.get("id") == toc_id:
                        found = it
                        break
                if not found:
                    errors.append(
                        EPUBValidationIssue(
                            level="error",
                            code="TOC_REF_INVALID",
                            message="spine@toc가 가리키는 item이 없습니다.",
                            path=opf_path,
                        )
                    )
                else:
                    href = found.get("href") or ""
                    joined = posixpath.normpath(posixpath.join(base_dir, href))
                    if joined not in zf.namelist():
                        errors.append(
                            EPUBValidationIssue(
                                level="error",
                                code="TOC_FILE_MISSING",
                                message="spine@toc가 가리키는 toc 파일이 없습니다.",
                                path=joined,
                            )
                        )
            else:
                warnings.append(
                    EPUBValidationIssue(
                        level="warning",
                        code="TOC_NOT_DECLARED",
                        message="EPUB2에서 spine@toc가 선언되지 않았습니다.",
                        path=opf_path,
                    )
                )

    except Exception as e:
        errors.append(
            EPUBValidationIssue(
                level="error",
                code="OPF_INVALID",
                message=f"content.opf 파싱 실패: {e}",
                path=opf_path,
            )
        )

    valid = len(errors) == 0
    return EPUBValidationResult(
        valid=valid, errors=errors, warnings=warnings, metadata=meta
    )
