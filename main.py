import os
import time
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Union
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import tiktoken
from notion_client import Client

# .env 파일에서 환경 변수 로드
load_dotenv()

# Notion 클라이언트 설정 (선택적)
notion = None
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if NOTION_TOKEN and NOTION_DATABASE_ID:
    try:
        notion = Client(auth=NOTION_TOKEN)
        print("✓ Notion 통합이 활성화되었습니다.")
    except Exception as e:
        print(f"⚠ Notion 클라이언트 초기화 실패: {str(e)}")
        print("  Notion 없이 계속 진행합니다.")
else:
    print("ℹ Notion 설정이 없습니다. Notion 저장 기능은 비활성화됩니다.")


# 상태 정의
class ConversationState(BaseModel):
    topic: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    summary: str = ""
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    title: str = ""
    subtitle: str = ""
    description: str = ""
    slug: str = ""
    notion_url: str = ""  # 새로운 필드 추가

# AI 현인 페르소나 정의


class AISage(BaseModel):
    name: str
    instruction: str
    color: str

# 토큰 계산 함수


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

# 비용 계산 함수


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    if model == "claude-3-opus-20240229":
        input_cost_per_1k = 0.015
        output_cost_per_1k = 0.075
    elif model == "claude-3-5-sonnet-20240620":
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
    else:
        raise ValueError("Unsupported model")

    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k
    return input_cost + output_cost


# 도구 정의


def get_topic(input: Union[str, None] = None) -> str:
    """사용자 입력 또는 뉴스 크롤링을 통해 주제를 가져옵니다."""
    if input:
        if input.startswith("http"):
            try:
                # URL이 주어진 경우, 웹 페이지의 제목을 가져옵니다
                response = requests.get(input)
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.title.string or "웹 페이지 제목을 찾을 수 없습니다"
            except:
                return "URL에서 주제를 가져오는데 실패했습니다"
        else:
            return input
    else:
        # 실제 구현에서는 여기에 뉴스 크롤링 로직을 추가합니다.
        return "최신 AI 기술 동향"


def generate_summary(conversation: List[Dict[str, str]]) -> str:
    """대화 내용을 요약합니다."""
    summary = "이 대화에서는 다음과 같은 주요 포인트가 논의되었습니다:\n"
    for i, message in enumerate(conversation, 1):
        summary += f"{i}. {message['content'][:50]}...\n"
    return summary


def create_content(summary: str, conversation: List[Dict[str, str]]) -> str:
    """요약과 대화 내용을 바탕으로 생동감 있는 콘텐츠를 생성합니다."""
    content = f"요약: {summary}\n\n대화 내용:\n\n"
    for message in conversation:
        content += f"{message['role']}: {message['content'][:100]}...\n\n"
    return content


def evaluate_conversation(state: ConversationState) -> bool:
    """대화의 충분성을 평가합니다."""
    return len(state.messages) >= 5 or state.cost >= 50.0


# LLM 모델 설정
# model = ChatAnthropic(model="claude-3-opus-20240229")
# model = ChatAnthropic(model="claude-3-5-sonnet-20240620")
# LLM 모델 설정
model_name = "claude-3-5-sonnet-20240620"
model = ChatAnthropic(model=model_name)


# JSON 파일에서 페르소나 로드
def load_personas(file_path: str) -> List[AISage]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return [AISage(**persona) for persona in data['personas']]

# 사용자가 페르소나 선택


def select_personas(personas: List[AISage]) -> List[AISage]:
    print("대화에 참여할 AI 현인을 선택하세요 (쉼표로 구분):")
    for i, persona in enumerate(personas, 1):
        print(f"{i}. {persona.name}")
    selections = input("선택: ").split(',')
    return [personas[int(s.strip()) - 1] for s in selections]


# 노드 함수 정의
# 노드 함수 수정
def initiate_conversation(state: ConversationState):
    topic = get_topic(state.topic)
    prompt = f"'{topic}'에 대해 토론을 시작해주세요."
    input_tokens = count_tokens(prompt)
    response = model.invoke(prompt)
    output_tokens = count_tokens(response.content)
    cost = calculate_cost(input_tokens, output_tokens, model_name)
    return ConversationState(
        topic=topic,
        messages=[{"role": "assistant", "content": response.content}],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost
    )


def continue_conversation(state: ConversationState, sages: List[AISage]):
    sage = sages[len(state.messages) % len(sages)]
    last_message = state.messages[-1]["content"]
    prompt = f"{sage.instruction} 이전 메시지를 고려하여 대화를 계속하세요: {last_message}"
    input_tokens = count_tokens(prompt)
    response = model.invoke(prompt)
    output_tokens = count_tokens(response.content)
    new_cost = state.cost + \
        calculate_cost(input_tokens, output_tokens, model_name)
    new_message = {"role": sage.name, "content": response.content}

    # 새 메시지를 출력합니다
    print_chat_message(new_message, sage.color)

    return ConversationState(
        topic=state.topic,
        messages=state.messages + [new_message],
        summary=state.summary,
        content=state.content,
        input_tokens=state.input_tokens + input_tokens,
        output_tokens=state.output_tokens + output_tokens,
        cost=new_cost
    )


# 노드 함수 수정 및 추가
def summarize_conversation(state: ConversationState):
    summary = generate_summary(state.messages)
    return ConversationState(**{**state.dict(), "summary": summary})


def generate_final_content(state: ConversationState):
    full_conversation = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in state.messages])
    prompt = f"""다음 대화를 정리하여 뉴욕타임즈 스타일의 기사를 작성해 보세요. 대화 내용은 다음과 같습니다:

{full_conversation}

이 대화를 바탕으로 뉴욕타임즈 스타일의 기사 본문을 작성해주세요."""

    input_tokens = count_tokens(prompt)
    response = model.invoke(prompt)
    output_tokens = count_tokens(response.content)
    new_cost = calculate_cost(input_tokens, output_tokens, model_name)

    return ConversationState(
        topic=state.topic,
        messages=state.messages,
        summary=state.summary,
        content=response.content.strip(),
        input_tokens=state.input_tokens + input_tokens,
        output_tokens=state.output_tokens + output_tokens,
        cost=state.cost + new_cost
    )


def generate_metadata(state: ConversationState):
    prompt = f"""다음 기사 내용을 바탕으로 제목, 부제목, 설명, 그리고 슬러그를 생성해주세요:

{state.content[:500]}...  # 내용이 너무 길 경우 앞부분만 사용

각 항목을 다음과 같은 형식으로 제공해주세요:
제목: [여기에 제목 입력]
부제목: [여기에 부제목 입력]
요약: [여기에 요약 입력]
슬러그: [여기에 슬러그 입력]"""

    try:
        input_tokens = count_tokens(prompt)
        response = model.invoke(prompt)
        output_tokens = count_tokens(response.content)
        new_cost = calculate_cost(input_tokens, output_tokens, model_name)

        # 응답에서 각 항목 추출
        lines = response.content.strip().split("\n")
        metadata = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()

        # 기본값 설정
        default_title = state.topic or "무제"
        default_subtitle = "AI가 생성한 기사"
        default_description = state.content[:100] + \
            "..." if state.content else "내용 없음"
        default_slug = "-".join(default_title.lower().split()[:5])

        return ConversationState(
            topic=state.topic,
            messages=state.messages,
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens + input_tokens,
            output_tokens=state.output_tokens + output_tokens,
            cost=state.cost + new_cost,
            title=metadata.get('제목', default_title),
            subtitle=metadata.get('부제목', default_subtitle),
            description=metadata.get('요약', default_description),
            slug=metadata.get('슬러그', default_slug)
        )
    except Exception as e:
        print(f"메타데이터 생성 중 오류 발생: {str(e)}")
        return ConversationState(
            topic=state.topic,
            messages=state.messages,
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
            cost=state.cost,
            title=state.topic or "무제",
            subtitle="AI가 생성한 기사",
            description=state.content[:100] +
            "..." if state.content else "내용 없음",
            slug="-".join((state.topic or "무제").lower().split()[:5])
        )


def save_to_notion(state: ConversationState):
    """노션에 생성된 콘텐츠를 저장합니다."""
    # Notion이 설정되지 않은 경우
    if not notion or not NOTION_DATABASE_ID:
        print("ℹ Notion 설정이 없어 저장을 건너뜁니다.")
        return ConversationState(
            topic=state.topic,
            messages=state.messages,
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
            cost=state.cost,
            title=state.title,
            subtitle=state.subtitle,
            description=state.description,
            slug=state.slug,
            notion_url="Notion 미설정"
        )

    try:
        # Notion 데이터베이스의 속성 구조 확인
        database = notion.databases.retrieve(NOTION_DATABASE_ID)
        properties = database.get('properties', {})

        # 페이지 속성 준비
        page_properties = {}

        # 제목 필드 찾기 및 설정
        title_field = next((k for k, v in properties.items()
                           if v['type'] == 'title'), None)
        if not title_field:
            raise ValueError("Title field not found in the database")

        page_properties[title_field] = {
            "title": [{"text": {"content": state.title}}]}

        # 다른 필드들 설정
        for field, value in [('Subtitle', state.subtitle), ('Description', state.description), ('Slug', state.slug)]:
            if field in properties:
                page_properties[field] = {
                    "rich_text": [{"text": {"content": value}}]}

        # 페이지 생성
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=page_properties,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": state.content}}]
                    }
                }
            ]
        )
        notion_url = f"https://www.notion.so/{new_page['id'].replace('-', '')}"

        # 상태 업데이트
        return ConversationState(
            topic=state.topic,
            messages=state.messages,
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
            cost=state.cost,
            title=state.title,
            subtitle=state.subtitle,
            description=state.description,
            slug=state.slug,
            notion_url=notion_url  # 새로운 필드 추가
        )
    except Exception as e:
        print(f"Notion에 저장 중 오류 발생: {str(e)}")
        # 오류 발생 시에도 상태 반환
        return ConversationState(
            topic=state.topic,
            messages=state.messages,
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens,
            output_tokens=state.output_tokens,
            cost=state.cost,
            title=state.title,
            subtitle=state.subtitle,
            description=state.description,
            slug=state.slug,
            notion_url="Notion 저장 실패"  # 오류 메시지
        )

# 워크플로우 수정


def create_workflow(sages: List[AISage]):
    workflow = StateGraph(ConversationState)
    workflow.add_node("initiate", initiate_conversation)
    workflow.add_node(
        "continue", lambda state: continue_conversation(state, sages))
    workflow.add_node("summarize", summarize_conversation)
    workflow.add_node("generate", generate_final_content)
    workflow.add_node("generate_metadata", generate_metadata)
    workflow.add_node("save_to_notion", save_to_notion)

    workflow.set_entry_point("initiate")

    workflow.add_conditional_edges(
        "initiate",
        should_continue,
        {
            "continue": "continue",
            "summarize": "summarize",
            "generate": "generate",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "continue",
        should_continue,
        {
            "continue": "continue",
            "summarize": "summarize",
            "generate": "generate",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "summarize",
        should_continue,
        {
            "generate": "generate",
            "end": END
        }
    )

    workflow.add_edge("generate", "generate_metadata")
    workflow.add_edge("generate_metadata", "save_to_notion")
    workflow.add_edge("save_to_notion", END)

    return workflow.compile()


# 상태 전이 함수


def should_continue(state: ConversationState):
    if not evaluate_conversation(state):
        return "continue"
    elif not state.summary:
        return "summarize"
    elif not state.content:
        return "generate"
    else:
        return "end"


# 채팅 메시지 출력 함수


def print_chat_message(message: Dict[str, str], color: str):
    role = message['role']
    content = message['content']

    # 메시지 출력
    print(f"\033[{color}m{role}: {content}\033[0m")
    print("-" * 50)  # 구분선
    time.sleep(1)  # 1초 대기

# 메인 함수 수정


def main():
    print("AI 현인 콘텐츠 생성기 테스트")

    # JSON 파일에서 페르소나 로드
    personas = load_personas('personas.json')

    # 사용자가 페르소나 선택
    selected_personas = select_personas(personas)

    print("1. 주제 직접 입력")
    print("2. URL 입력")
    print("3. 자동 주제 선택")
    choice = input("선택하세요 (1/2/3): ")

    if choice == "1":
        topic = input("주제를 입력하세요: ")
    elif choice == "2":
        topic = input("URL을 입력하세요: ")
    else:
        topic = None

    # get_topic 함수를 사용하여 항상 유효한 문자열 주제를 얻습니다
    final_topic = get_topic(topic)
    print(f"\n선택된 주제: {final_topic}\n")

    print("대화 시작...")
    graph = create_workflow(selected_personas)
    result = graph.invoke({"topic": final_topic})

    print("\n생성된 뉴욕타임즈 스타일 기사:")
    if isinstance(result, ConversationState):
        print(f"제목: {result.title}")
        print(f"부제목: {result.subtitle}")
        print(f"설명: {result.description}")
        print(f"슬러그: {result.slug}")
        print("\n본문:")
        print(result.content)
        print(f"\n총 입력 토큰: {result.input_tokens}")
        print(f"총 출력 토큰: {result.output_tokens}")
        print(f"총 비용: ${result.cost:.4f}")
        print(f"\n노션 페이지 URL: {result.notion_url}")
    else:
        print("예상치 못한 결과 형식입니다.")
        print(result)  # 디버깅을 위해 전체 결과 출력


if __name__ == "__main__":
    main()
