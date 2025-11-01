from pydantic import BaseModel, Field
from typing import List

# 캘린더에 들어갈 상세 일정 정보를 위한 구조
class NextSchedule(BaseModel):
    """
    회의에서 결정된 다음 회의 또는 후속 일정에 대한 상세 정보를 정의하는 Pydantic 모델.
    이는 캘린더 이벤트 생성에 사용됩니다.
    """
    next_schedule_date: str = Field(
        ...,
        description="다음 회의 또는 후속 일정의 날짜. 반드시 YYYY-MM-DD 형식으로 추출할 것."
    )
    start_time: str = Field(
        "10:00",
        description="일정 시작 시간. HH:MM 형식 (24시간)."
    )
    end_time: str = Field(
        "11:00",
        description="일정 종료 시간. HH:MM 형식 (24시간)." 
    )
    event_title: str = Field(
        ...,
        description="추출된 다음 회의 또는 후속 일정의 구글 캘린더 제목(Title/Summary)."
    )
    event_content: str = Field(
        ...,
        description="추출된 다음 회의 또는 후속 일정의 구글 캘린더 내용/본문(Content/Description). 2~3줄로 작성."
    )
    event_location: str = Field(
        "", 
        description="후속 일정의 장소. 예: 1회의실, 온라인(Google Meet), 강남 지사 등. 명시되지 않은 경우 빈 문장열('') 사용"
    )

# 회의록 전체 분석 결과를 위한 최종 JSON 구조
class MeetingAnalysisResult(BaseModel):
    """
    Gemini API를 통해 추출하고자 하는 회의록 분석의 최종 JSON 구조를 정의하는 Pydantic 모델.
    """
    meeting_summary: str = Field(
        ...,
        description="회의록 전체 내용에 대한 3~4줄 핵심 요약."
    )
    # List[NextSchedule]을 사용하여 캘린더 일정 객체의 리스트를 명시적으로 나타냅니다.
    next_schedules: List[NextSchedule] = Field(
        ...,
        description="회의에서 결정된 다음 회의 또는 일정 정보 리스트."
    )