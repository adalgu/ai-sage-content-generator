from typing import List
from typing import List, Dict, Any
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
import streamlit as st
from typing import List, Dict, Any

# .env 파일에서 환경 변수 로드
load_dotenv()

# Notion 클라이언트 설정
notion = Client(auth=os.getenv("NOTION_TOKEN"))
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

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
    notion_url: str = ""

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
    if input:
        if input.startswith("http"):
            try:
                response = requests.get(input)
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.title.string or "웹 페이지 제목을 찾을 수 없습니다"
            except:
                return "URL에서 주제를 가져오는데 실패했습니다"
        else:
            return input
    else:
        return "최신 AI 기술 동향"


def generate_summary(conversation: List[Dict[str, str]]) -> str:
    summary = "이 대화에서는 다음과 같은 주요 포인트가 논의되었습니다:\n"
    for i, message in enumerate(conversation, 1):
        summary += f"{i}. {message['content'][:50]}...\n"
    return summary


def create_content(summary: str, conversation: List[Dict[str, str]]) -> str:
    content = f"요약: {summary}\n\n대화 내용:\n\n"
    for message in conversation:
        content += f"{message['role']}: {message['content'][:100]}...\n\n"
    return content


def evaluate_conversation(state: ConversationState) -> bool:
    return len(state.messages) >= 5 or state.cost >= 50.0


# LLM 모델 설정
model_name = "claude-3-5-sonnet-20240620"
model = ChatAnthropic(model=model_name)

# JSON 파일에서 페르소나 로드


def load_personas(file_path: str) -> List[AISage]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return [AISage(**persona) for persona in data['personas']]

# 노드 함수 정의


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


def get_messages(state: Any) -> List[Dict[str, str]]:
    if isinstance(state, ConversationState):
        return state.messages
    elif isinstance(state, dict) and 'messages' in state:
        return state['messages']
    else:
        return []


def get_state_value(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, ConversationState):
        return getattr(state, key, default)
    elif isinstance(state, dict):
        return state.get(key, default)
    else:
        return default


def continue_conversation(state: Any, sages: List[AISage]) -> Any:
    messages = get_messages(state)
    sage = sages[len(messages) % len(sages)]
    last_message = messages[-1]["content"] if messages else ""
    prompt = f"{sage.instruction} 이전 메시지를 고려하여 대화를 계속하세요: {last_message}"
    input_tokens = count_tokens(prompt)
    response = model.invoke(prompt)
    output_tokens = count_tokens(response.content)
    new_cost = calculate_cost(input_tokens, output_tokens, model_name)
    new_message = {"role": sage.name, "content": response.content}

    if isinstance(state, ConversationState):
        return ConversationState(
            topic=state.topic,
            messages=state.messages + [new_message],
            summary=state.summary,
            content=state.content,
            input_tokens=state.input_tokens + input_tokens,
            output_tokens=state.output_tokens + output_tokens,
            cost=state.cost + new_cost
        )
    elif isinstance(state, dict):
        new_state = state.copy()
        new_state['messages'] = state.get('messages', []) + [new_message]
        new_state['input_tokens'] = state.get('input_tokens', 0) + input_tokens
        new_state['output_tokens'] = state.get(
            'output_tokens', 0) + output_tokens
        new_state['cost'] = state.get('cost', 0.0) + new_cost
        return new_state
    else:
        raise ValueError("Unexpected state type")


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
        st.error(f"메타데이터 생성 중 오류 발생: {str(e)}")
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
    try:
        database = notion.databases.retrieve(NOTION_DATABASE_ID)
        properties = database.get('properties', {})

        page_properties = {}

        title_field = next((k for k, v in properties.items()
                           if v['type'] == 'title'), None)
        if not title_field:
            raise ValueError("Title field not found in the database")

        page_properties[title_field] = {
            "title": [{"text": {"content": state.title}}]}

        for field, value in [('Subtitle', state.subtitle), ('Description', state.description), ('Slug', state.slug)]:
            if field in properties:
                page_properties[field] = {
                    "rich_text": [{"text": {"content": value}}]}

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
            notion_url=notion_url
        )
    except Exception as e:
        st.error(f"Notion에 저장 중 오류 발생: {str(e)}")
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
            notion_url="Notion 저장 실패"
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


def should_continue(state: ConversationState):
    if not evaluate_conversation(state):
        return "continue"
    elif not state.summary:
        return "summarize"
    elif not state.content:
        return "generate"
    else:
        return "end"


def run_workflow(graph, initial_state: ConversationState, selected_persona_objects: List[AISage]):
    conversation_history = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()

    steps = ["initiate", "continue", "summarize",
             "generate", "generate_metadata", "save_to_notion"]
    total_steps = len(steps)

    # 초기 상태 설정
    state = initial_state

    for i, step in enumerate(steps):
        progress = (i + 1) / total_steps
        progress_bar.progress(progress)
        status_text.text(f"진행 중: {step}")

        if step == "continue":
            for _ in range(len(selected_persona_objects)):
                state = continue_conversation(state, selected_persona_objects)
                messages = get_messages(state)
                conversation_history.markdown(
                    "\n".join([f"**{msg['role']}**: {msg['content']}" for msg in messages]))
                time.sleep(0.5)
        else:
            state = graph.invoke(state)

        messages = get_messages(state)
        conversation_history.markdown(
            "\n".join([f"**{msg['role']}**: {msg['content']}" for msg in messages]))

        if step == "generate":
            break  # generate 단계 후 중단

        time.sleep(0.5)  # 진행 상황을 보기 위한 짧은 지연

    return state


def main():
    st.title("AI 현인 콘텐츠 생성기")

    # JSON 파일에서 페르소나 로드
    personas = load_personas('personas.json')

    # 사이드바에 페르소나 선택 옵션 추가
    selected_personas = st.sidebar.multiselect(
        "대화에 참여할 AI 현인을 선택하세요",
        options=[persona.name for persona in personas],
        default=[personas[0].name]
    )

    # 선택된 페르소나 객체 리스트 생성
    selected_persona_objects = [
        persona for persona in personas if persona.name in selected_personas
    ]

    # 주제 입력 방식 선택
    topic_input_method = st.radio(
        "주제 입력 방식을 선택하세요:",
        ("직접 입력", "URL 입력", "자동 주제 선택")
    )

    if topic_input_method == "직접 입력":
        topic = st.text_input("주제를 입력하세요:")
    elif topic_input_method == "URL 입력":
        topic = st.text_input("URL을 입력하세요:")
    else:
        topic = None

    # 대화 시작 버튼
    if st.button("대화 시작"):
        if not selected_persona_objects:
            st.warning("적어도 하나의 AI 현인을 선택해주세요.")
        else:
            # get_topic 함수를 사용하여 유효한 문자열 주제를 얻습니다
            final_topic = get_topic(topic)
            st.write(f"선택된 주제: {final_topic}")

            # 워크플로우 생성
            graph = create_workflow(selected_persona_objects)

            # 초기 상태 생성
            initial_state = ConversationState(topic=final_topic)

            # 워크플로우 실행
            final_state = run_workflow(
                graph, initial_state, selected_persona_objects)

            # 최종 결과 표시
            st.success("콘텐츠 생성 완료!")
            st.write("## 생성된 뉴욕타임즈 스타일 기사")
            st.write(
                f"**제목:** {get_state_value(final_state, 'title', '제목 없음')}")
            st.write(
                f"**부제목:** {get_state_value(final_state, 'subtitle', '부제목 없음')}")
            st.write(
                f"**설명:** {get_state_value(final_state, 'description', '설명 없음')}")
            st.write(
                f"**슬러그:** {get_state_value(final_state, 'slug', '슬러그 없음')}")
            st.write("### 본문:")
            st.write(get_state_value(final_state, 'content', '본문 없음'))
            st.write(
                f"**총 입력 토큰:** {get_state_value(final_state, 'input_tokens', 0)}")
            st.write(
                f"**총 출력 토큰:** {get_state_value(final_state, 'output_tokens', 0)}")
            st.write(
                f"**총 비용:** ${get_state_value(final_state, 'cost', 0.0):.4f}")
            st.write(
                f"**노션 페이지 URL:** {get_state_value(final_state, 'notion_url', 'URL 없음')}")


if __name__ == "__main__":
    main()
