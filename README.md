# AI 현인 콘텐츠 생성기

AI 현인 콘텐츠 생성기는 다양한 AI 페르소나를 활용하여 주어진 주제에 대한 대화를 생성하고, 이를 바탕으로 원하는 스타일(ex. 뉴욕타임즈 스타일)의 기사를 작성하는 프로젝트입니다.

## 기능

- 다양한 AI 페르소나 (철학자, 과학자, 윤리학자 등) 간의 대화 생성
- 사용자 지정 주제 또는 URL에서 추출한 주제로 대화 시작
- 생성된 대화를 바탕으로 원하는 스타일의 기사 작성
- 토큰 사용량 및 비용 계산

## 기술 스택

- **Python**: 주 프로그래밍 언어
- **LangChain**: 대규모 언어 모델(LLM)을 사용한 애플리케이션 개발을 위한 프레임워크
- **LangGraph**: LangChain 기반의 그래프 구조 구현을 위한 라이브러리
- **Anthropic Claude**: 고성능 대화형 AI 모델
- **Pydantic**: 데이터 유효성 검사 및 설정 관리
- **Tiktoken**: OpenAI의 토큰화 라이브러리
- **Requests**: HTTP 라이브러리
- **Beautiful Soup**: 웹 스크래핑을 위한 라이브러리
- **python-dotenv**: 환경 변수 관리

## 설치 방법

1. 이 저장소를 클론합니다:

   ```
   git clone https://github.com/your-username/ai-sage-content-generator.git
   ```

2. 프로젝트 디렉토리로 이동합니다:

   ```
   cd ai-sage-content-generator
   ```

3. 필요한 패키지를 설치합니다:

   ```
   pip install -r requirements.txt
   ```

4. `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:

   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

5. `personas.json` 파일을 생성하고 AI 페르소나를 정의합니다.

## 사용 방법

1. 다음 명령어로 프로그램을 실행합니다:

   ```
   python main.py
   ```

2. 프롬프트에 따라 대화에 참여할 AI 페르소나를 선택합니다.

3. 주제 입력 방식을 선택하고 주제를 입력합니다.

4. 생성된 대화와 최종 기사를 확인합니다.

## 주의사항

- 이 프로젝트는 Anthropic의 API를 사용합니다. API 사용에 따른 비용이 발생할 수 있으므로 주의하세요.
- `personas.json` 파일에 민감한 정보를 포함하지 않도록 주의하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여

버그 리포트, 기능 제안, 풀 리퀘스트는 언제나 환영합니다. 프로젝트에 기여하고 싶으시다면 이슈를 열어 논의를 시작해주세요.
