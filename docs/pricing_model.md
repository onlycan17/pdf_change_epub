# LLM 사용량 기반 가격 산정 모델 설계

## 1. 목표
- LLM과 OCR 호출 비용을 투명하게 반영하는 사용량 기반 과금 체계를 수립합니다.
- 무료 체험 구간을 제공하면서, 고용량·고품질 변환에 대해서는 합리적인 과금을 적용합니다.
- Supabase 인프라(Managed Postgres/Storage)로 사용량 기록과 결제 단계를 추적합니다.

## 2. 사용량 지표
| 항목 | 설명 | 추적 방법 |
| ---- | ---- | --------- |
| `tokens_prompt` | LLM에 전달한 입력 토큰 수 | OpenRouter API 응답의 usage.prompt_tokens |
| `tokens_completion` | LLM 응답 토큰 수 | OpenRouter API 응답의 usage.completion_tokens |
| `ocr_pages` | OCR가 수행된 페이지 수 | 변환 파이프라인에서 Page 단위 기록 |
| `total_pages` | 변환된 PDF 총 페이지 수 | PDF Analyzer 결과 |
| `execution_time` | 변환 파이프라인 총 처리 시간(초) | Celery 작업 종료 시 기록 |
| `storage_size` | 최종 EPUB 및 중간 산출물 크기 | Supabase Storage 메타데이터 |

## 3. 비용 요소
1. **LLM 비용**
   - 기본 단가: `$0.0008` / 1K 토큰 (OpenRouter 예시)
   - 청구 토큰: `tokens_prompt + tokens_completion`
2. **OCR 비용**
   - PaddleOCR 자체 사용료는 없으나 GPU/CPU 리소스를 반영하기 위해 페이지당 `$0.001`
3. **인프라 마진**
   - Storage/네트워크/운영비 포함하여 결과 파일 크기 1MB당 `$0.0005`
4. **고정 수수료**
   - 결제 처리 수수료 및 기본 운영비로 건당 `$0.05`

## 4. 가격 공식
```
llm_cost = (tokens_prompt + tokens_completion) / 1000 * 0.0008
ocr_cost = ocr_pages * 0.001
storage_cost = (epub_size_mb + intermediate_size_mb) * 0.0005
variable_cost = llm_cost + ocr_cost + storage_cost

# 마진(20%)를 적용한 총 비용
usage_cost = variable_cost * 1.2 + 0.05
```
- 무료 구간: 매월 `usage_cost` 기준 첫 `$1`까지 차감
- 최소 청구 금액: $0.30 (무료 구간 초과 시)

## 5. 제공 플랜
| 플랜 | 기준 | 포함량 | 초과 시 |
| ---- | ---- | ------ | ------- |
| Free | 월간 사용량 `$1` 이하 | LLM 15K 토큰, OCR 100페이지, 결과 200MB | 초과분은 Basic 요율 적용 |
| Basic | 월 $9 | LLM 200K 토큰, OCR 1,000페이지, 결과 2GB | 초과분은 사용량 기반 과금 |
| Pro | 월 $29 | LLM 800K 토큰, OCR 5,000페이지, 결과 10GB | 초과분 사용량 기반 과금, 우선 지원 |

- 초과 과금은 `usage_cost - plan_credit`을 월말에 결제 (plan_credit은 포함량에 해당하는 비용).
- 플랜 전환 시 남은 크레딧은 이월되지 않고 다음 청구 주기부터 새 플랜 기준 적용.

## 6. 사용량 기록 & 결제 연동 흐름
1. Celery 작업 완료 시 Supabase `conversion_usage` 테이블에 다음을 INSERT
   ```sql
   INSERT INTO conversion_usage (
     job_id, user_id, tokens_prompt, tokens_completion,
     ocr_pages, total_pages, epub_size_mb, intermediate_size_mb,
     usage_cost, created_at
   )
   VALUES (...)
   ```
2. 월말 배치 작업 (Supabase Edge Function + Scheduled Trigger)
   - 사용자별로 usage_cost 합산
   - 플랜 크레딧 차감 후 초과분 계산
   - Stripe/PortOne 결제 API 호출 요청 준비 (추후 결제 작업과 연계)
3. 결제 성공 시 `billing_invoice` 테이블 업데이트, 실패 시 재시도 및 알림 발송

## 7. 추후 고려 사항
- LLM 모델별로 단가가 다를 경우 `model_cost_multiplier` 필드를 두어 가중치를 적용
- PDF 페이지 수와 변환 난이도(레이아웃 복잡도 등)에 따라 OCR/LLM 호출 정책을 다르게 적용하는 옵션 추가
- 기업 고객을 위한 프라이빗 플랜: 고정 월 요금 + 초과 사용량 할인율 제공
