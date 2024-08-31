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


# .env 파일에서 환경 변수 로드
load_dotenv()

# 상태 정의


class ConversationState(BaseModel):
    topic: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    summary: str = ""
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0

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
    prompt = f"다음 대화를 정리하여 뉴욕타임즈 스타일의 기사를 작성해 보세요. 대화 내용은 다음과 같습니다:\n\n{full_conversation}\n\n이 대화를 바탕으로 뉴욕타임즈 스타일의 기사를 작성해주세요."

    input_tokens = count_tokens(prompt)
    response = model.invoke(prompt)
    output_tokens = count_tokens(response.content)
    new_cost = calculate_cost(input_tokens, output_tokens, model_name)

    return ConversationState(
        topic=state.topic,
        messages=state.messages,
        summary=state.summary,
        content=response.content,
        input_tokens=state.input_tokens + input_tokens,
        output_tokens=state.output_tokens + output_tokens,
        cost=state.cost + new_cost
    )

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


# 그래프 정의 수정
def create_workflow(sages: List[AISage]):
    workflow = StateGraph(ConversationState)
    workflow.add_node("initiate", initiate_conversation)
    workflow.add_node(
        "continue", lambda state: continue_conversation(state, sages))
    workflow.add_node("summarize", summarize_conversation)
    workflow.add_node("generate", generate_final_content)

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

    workflow.add_edge("generate", END)

    return workflow.compile()


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
    if isinstance(result, dict):
        if 'content' in result:
            print(result['content'])
        else:
            print("콘텐츠를 찾을 수 없습니다.")

        print(f"\n총 입력 토큰: {result.get('input_tokens', 'N/A')}")
        print(f"총 출력 토큰: {result.get('output_tokens', 'N/A')}")
        print(f"총 비용: ${result.get('cost', 0):.4f}")
    else:
        print("예상치 못한 결과 형식입니다.")
        print(result)  # 디버깅을 위해 전체 결과 출력


if __name__ == "__main__":
    main()
# # 메인 함수 수정


# def main():
#     print("AI 현인 콘텐츠 생성기 테스트")

#     # JSON 파일에서 페르소나 로드
#     personas = load_personas('personas.json')

#     # 사용자가 페르소나 선택
#     selected_personas = select_personas(personas)

#     print("1. 주제 직접 입력")
#     print("2. URL 입력")
#     print("3. 자동 주제 선택")
#     choice = input("선택하세요 (1/2/3): ")

#     if choice == "1":
#         topic = input("주제를 입력하세요: ")
#     elif choice == "2":
#         topic = input("URL을 입력하세요: ")
#     else:
#         topic = None

#     # get_topic 함수를 사용하여 항상 유효한 문자열 주제를 얻습니다
#     final_topic = get_topic(topic)
#     print(f"\n선택된 주제: {final_topic}\n")

#     print("대화 시작...")
#     graph = create_workflow(selected_personas)
#     result = graph.invoke({"topic": final_topic})

#     print("\n생성된 뉴욕타임즈 스타일 기사:")
#     if isinstance(result, dict) and 'ConversationState' in result:
#         state = result['ConversationState']
#         if isinstance(state, ConversationState):
#             print(state.content)
#             print(f"\n총 입력 토큰: {state.input_tokens}")
#             print(f"총 출력 토큰: {state.output_tokens}")
#             print(f"총 비용: ${state.cost:.4f}")
#         elif isinstance(state, dict):
#             print(state.get('content', '콘텐츠를 찾을 수 없습니다.'))
#             print(f"\n총 입력 토큰: {state.get('input_tokens', 'N/A')}")
#             print(f"총 출력 토큰: {state.get('output_tokens', 'N/A')}")
#             print(f"총 비용: ${state.get('cost', 0):.4f}")
#     else:
#         print("예상치 못한 결과 형식입니다.")
#         print(result)  # 디버깅을 위해 전체 결과 출력

#     # 토큰 사용량과 비용 출력
#     if isinstance(result, dict) and 'ConversationState' in result:
#         state = result['ConversationState']
#         if isinstance(state, ConversationState):
#             print(f"\n총 입력 토큰: {state.input_tokens}")
#             print(f"총 출력 토큰: {state.output_tokens}")
#             print(f"총 비용: ${state.cost:.4f}")
#         elif isinstance(state, dict):
#             print(f"\n총 입력 토큰: {state.get('input_tokens', 'N/A')}")
#             print(f"총 출력 토큰: {state.get('output_tokens', 'N/A')}")
#             print(f"총 비용: ${state.get('cost', 0):.4f}")
#     else:
#         print("\n토큰 사용량과 비용을 계산할 수 없습니다.")


# if __name__ == "__main__":
#     main()
