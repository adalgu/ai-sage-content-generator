import unittest
from unittest.mock import Mock, patch
from pydantic import BaseModel

# main.py에서 필요한 함수와 변수를 임포트합니다
from main import save_to_notion, ConversationState, notion, NOTION_DATABASE_ID


class TestSaveToNotion(unittest.TestCase):

    @patch('main.notion')
    @patch('main.NOTION_DATABASE_ID', 'test-database-id')
    def test_save_to_notion_success(self, mock_notion):
        # 성공 케이스 설정
        mock_database = {
            'properties': {
                'Name': {'type': 'title'},
                'Subtitle': {'type': 'rich_text'},
                'Description': {'type': 'rich_text'},
                'Slug': {'type': 'rich_text'}
            }
        }
        mock_notion.databases.retrieve.return_value = mock_database
        mock_notion.pages.create.return_value = {'id': 'test-page-id'}

        # 테스트 데이터
        state = ConversationState(
            topic="Test Topic",
            messages=[],
            summary="",
            content="Test Content",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            title="Test Title",
            subtitle="Test Subtitle",
            description="Test Description",
            slug="test-slug"
        )

        # 함수 실행
        result = save_to_notion(state)

        # 검증
        self.assertEqual(result, "https://www.notion.so/testpageid")
        mock_notion.pages.create.assert_called_once()

    @patch('main.notion')
    @patch('main.NOTION_DATABASE_ID', 'test-database-id')
    def test_save_to_notion_missing_title(self, mock_notion):
        # 제목 필드가 없는 경우
        mock_database = {
            'properties': {
                'Subtitle': {'type': 'rich_text'},
                'Description': {'type': 'rich_text'},
                'Slug': {'type': 'rich_text'}
            }
        }
        mock_notion.databases.retrieve.return_value = mock_database
        mock_notion.pages.create.side_effect = Exception("Missing title field")

        state = ConversationState(
            topic="Test Topic",
            messages=[],
            summary="",
            content="Test Content",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            title="Test Title",
            subtitle="Test Subtitle",
            description="Test Description",
            slug="test-slug"
        )

        result = save_to_notion(state)

        self.assertEqual(result, "Notion 저장 실패")

    @patch('main.notion')
    @patch('main.NOTION_DATABASE_ID', 'test-database-id')
    def test_save_to_notion_api_error(self, mock_notion):
        # API 오류 시뮬레이션
        mock_notion.databases.retrieve.side_effect = Exception("API Error")

        state = ConversationState(
            topic="Test Topic",
            messages=[],
            summary="",
            content="Test Content",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            title="Test Title",
            subtitle="Test Subtitle",
            description="Test Description",
            slug="test-slug"
        )

        result = save_to_notion(state)

        self.assertEqual(result, "Notion 저장 실패")


if __name__ == '__main__':
    unittest.main()
