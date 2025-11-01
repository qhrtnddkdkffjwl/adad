import os
import json
from datetime import datetime, date
import sys

# STT 모듈에서 텍스트 변환 함수를 임포트합니다. 
from stt_module import run_stt_conversion 

# Gemini API 클라이언트 및 타입 임포트
from google.genai import Client, types
from pydantic import ValidationError

# Pydantic 클래스 임포트
from data_schema import MeetingAnalysisResult 

# ----------------------------------------------------
# 0. 전역 설정 및 상수
# ----------------------------------------------------
AUDIO_FILE = "voice.m4a"
GEMINI_MODEL = 'gemini-2.5-flash'
DEFAULT_EMPTY_STRING = ""
TODAY_DATE = date.today().strftime("%Y년 %m월 %d일") # 날짜 추론을 위한 현재 날짜 제공

# ----------------------------------------------------
# 1. GEMINI 구조화 분석 로직
# ----------------------------------------------------

# API 클라이언트 초기화 및 검증
try:
    if not os.getenv("GEMINI_API_KEY"):
         raise EnvironmentError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 시스템 환경 변수를 확인하세요.")
         
    client = Client()
    print("Gemini Client 초기화 완료.")
except Exception as e:
    print(f"[초기화 오류] 클라이언트 초기화 중 문제 발생: {e}")
    sys.exit(1) # 클라이언트 초기화 실패 시 시스템 종료

def extract_meeting_data(meeting_text: str) -> dict | None:
    """
    회의록 텍스트를 받아 구조화된 JSON 데이터를 추출합니다.
    """
    
    # 2. 프롬프트 정의
    prompt = f"""
    당신은 전문 회의록 분석가입니다. 다음 회의록 텍스트를 분석하여,
    제공된 **MeetingAnalysisResult** JSON 스키마에 따라 데이터를 정확하게 추출하세요.

    **[핵심 정보 제공]**
    현재 날짜는 {TODAY_DATE} 입니다.

    **[추출 지침: 구조화 엄수]**
    분석 결과는 반드시 제공된 JSON 스키마의 중첩 구조를 100% 따라야 합니다.
    JSON 출력 외의 다른 설명이나 부연설명은 일절 추가하지 마세요.

    **[추출 지시 사항]**
    1. **'meeting_summary'**: 회의록 전체 내용에 대한 간결하고 핵심적인 요약(3~4줄)을 작성하세요.
    2. **'next_schedules'**: 회의록에 언급된 **모든** 후속 일정은 이 리스트에 별도의 객체로 포함되어야 합니다.
        a. **next_schedule_date**: 후속 일정의 날짜를 **YYYY-MM-DD** 형식으로 추출하세요. 날짜가 '다음 주 수요일'처럼 모호할 경우, **현재 날짜({TODAY_DATE})를 기준으로 논리적으로 추론**하여 날짜를 결정해야 합니다.
        b. **start_time**: 후속 일정의 시작 시간을 **HH:MM** 형식으로 추출하세요. 시간이 명시되지 않았다면, **회의록의 문맥(오전/오후)을 파악하여 가장 합리적인 HH:MM 시간으로 추론**해야 합니다.
        c. **end_time**: 후속 일정의 종료 시간을 **HH:MM** 형식으로 추출하세요. 종료 시간이 명시되지 않았다면, **시작 시간을 기준으로 +1 시간을 계산하여 추론**하여 제공해야 합니다.
        d. **event_title**: 구글 캘린더 이벤트의 **제목 (Title/Summary)**에 들어갈 핵심 제목을 추출하세요.
        e. **event_content**: 구글 캘린더 이벤트의 **내용/본문 (Content/Description)**에 들어갈 상세 설명을 **2~3줄**로 작성하세요.
        f. **event_location**: 회의록에서 장소를 추출하세요. 명시적으로 언급되지 않았다면, **반드시 빈 문자열 (`"{DEFAULT_EMPTY_STRING}"`)을 값으로 사용**하세요.
    
    분석 결과는 반드시 제공된 JSON 스키마의 중첩 구조를 따라야 합니다.
    ---
    회의록 텍스트:
    {meeting_text}
    """
    
    # 3. 모델 설정 및 API 호출
    print(f"   -> Gemini 모델 호출 시작 ({GEMINI_MODEL})...")
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MeetingAnalysisResult,
            )
        )
        
        # 4. JSON 문자열을 파이썬 딕셔너리로 변환 및 Pydantic 유효성 검사
        json_data = response.text.strip()
        parsed_data = MeetingAnalysisResult.model_validate_json(json_data).model_dump()
        print("Gemini 분석 및 Pydantic 유효성 검사 성공.")
        return parsed_data
    
    except ValidationError as e:
        print(f"[Gemini Error] Pydantic 유효성 검사 오류: 모델이 스키마를 따르지 않았습니다.")
        print(f"   오류 상세: {e}")
        return None
    except Exception as e:
        print(f"[Gemini Error] Gemini API 호출 중 오류 발생: {e}")
        return None

# ----------------------------------------------------
# 4. 메인 실행 로직
# ----------------------------------------------------

def main():
    print(f"\n--- 1단계: STT 모듈 호출 및 텍스트 추출 ({AUDIO_FILE}) ---")
    
    # stt_module.py의 함수를 호출하여 텍스트를 받습니다.
    meeting_transcript = run_stt_conversion(AUDIO_FILE) 

    # STT 결과가 없으면 분석을 중단하고 종료합니다.
    if not meeting_transcript:
        print("STT 변환 실패 또는 오디오 파일 부재로 Gemini 분석을 건너뛰고 종료합니다.")
        return
    
    print("   -> STT 변환 텍스트: " + meeting_transcript[:80].strip() + "..." ) # 변환된 텍스트 일부 출력

    print("\n--- 2단계: Gemini API로 텍스트 분석 및 구조화 ---")
    extracted_data = extract_meeting_data(meeting_transcript)

    if extracted_data:
        # ----------------------------------------------------
        # JSON 파일 저장 로직
        # ----------------------------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"analysis_output_{timestamp}.json"
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=4)
            print(f"\nJSON 파일 저장 성공: {output_filename}")
        except IOError as e:
            print(f"[파일 저장 오류] JSON 파일 저장 실패: {e}")

        print("\n**[ 최종 Gemini 분석 데이터 ]**")
        # 최종 JSON 데이터를 보기 좋게 출력
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        print("-----------------------------------")
    else:
        print("최종 데이터 추출에 실패했습니다. (Gemini 또는 Pydantic 오류 확인)")

if __name__ == "__main__":
    main()