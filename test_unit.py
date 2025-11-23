"""
Unit tests for AI Sage Content Generator
"""

import pytest
import json
from unittest.mock import Mock, patch
from main import (
    count_tokens,
    calculate_cost,
    get_topic,
    load_personas,
    AISage,
    ConversationState,
    evaluate_conversation
)


class TestTokenFunctions:
    """Tests for token counting and cost calculation"""

    def test_count_tokens_empty_string(self):
        """Test token counting with empty string"""
        result = count_tokens("")
        assert result == 0

    def test_count_tokens_simple_string(self):
        """Test token counting with simple string"""
        result = count_tokens("Hello, world!")
        assert result > 0
        assert isinstance(result, int)

    def test_count_tokens_korean(self):
        """Test token counting with Korean text"""
        result = count_tokens("안녕하세요")
        assert result > 0
        assert isinstance(result, int)


class TestCostCalculation:
    """Tests for cost calculation"""

    def test_calculate_cost_sonnet(self):
        """Test cost calculation for Claude 3.5 Sonnet"""
        # 1000 input tokens, 1000 output tokens
        cost = calculate_cost(1000, 1000, "claude-3-5-sonnet-20240620")
        expected = (1000/1000 * 0.003) + (1000/1000 * 0.015)  # $0.018
        assert cost == pytest.approx(expected)

    def test_calculate_cost_opus(self):
        """Test cost calculation for Claude 3 Opus"""
        cost = calculate_cost(1000, 1000, "claude-3-opus-20240229")
        expected = (1000/1000 * 0.015) + (1000/1000 * 0.075)  # $0.09
        assert cost == pytest.approx(expected)

    def test_calculate_cost_unsupported_model(self):
        """Test cost calculation with unsupported model"""
        with pytest.raises(ValueError):
            calculate_cost(1000, 1000, "unsupported-model")

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        cost = calculate_cost(0, 0, "claude-3-5-sonnet-20240620")
        assert cost == 0.0


class TestGetTopic:
    """Tests for topic retrieval"""

    def test_get_topic_direct_input(self):
        """Test with direct topic input"""
        topic = get_topic("AI and Machine Learning")
        assert topic == "AI and Machine Learning"

    def test_get_topic_none_input(self):
        """Test with None input (default topic)"""
        topic = get_topic(None)
        assert topic == "최신 AI 기술 동향"

    def test_get_topic_empty_input(self):
        """Test with empty string input"""
        topic = get_topic("")
        assert topic == ""

    @patch('main.requests.get')
    def test_get_topic_url_success(self, mock_get):
        """Test URL topic extraction with successful response"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.text = '<html><head><title>Test Title</title></head></html>'
        mock_get.return_value = mock_response

        topic = get_topic("http://example.com")
        assert topic == "Test Title"

    @patch('main.requests.get')
    def test_get_topic_url_failure(self, mock_get):
        """Test URL topic extraction with failed response"""
        # Mock failed HTTP response
        mock_get.side_effect = Exception("Network error")

        topic = get_topic("http://example.com")
        assert topic == "URL에서 주제를 가져오는데 실패했습니다"


class TestPersonaLoading:
    """Tests for persona loading"""

    def test_load_personas_valid_file(self):
        """Test loading personas from valid JSON file"""
        personas = load_personas('personas.json')

        assert isinstance(personas, list)
        assert len(personas) > 0

        # Check first persona structure
        first_persona = personas[0]
        assert isinstance(first_persona, AISage)
        assert hasattr(first_persona, 'name')
        assert hasattr(first_persona, 'instruction')
        assert hasattr(first_persona, 'color')

    def test_load_personas_count(self):
        """Test that correct number of personas are loaded"""
        personas = load_personas('personas.json')
        # Based on personas.json, should have 10 personas
        assert len(personas) == 10

    def test_persona_names(self):
        """Test that key personas are loaded"""
        personas = load_personas('personas.json')
        persona_names = [p.name for p in personas]

        assert "워렌 버핏" in persona_names
        assert "일론 머스크" in persona_names
        assert "레이 달리오" in persona_names


class TestConversationState:
    """Tests for ConversationState model"""

    def test_conversation_state_creation(self):
        """Test creating a basic conversation state"""
        state = ConversationState(topic="Test Topic")

        assert state.topic == "Test Topic"
        assert state.messages == []
        assert state.summary == ""
        assert state.content == ""
        assert state.input_tokens == 0
        assert state.output_tokens == 0
        assert state.cost == 0.0

    def test_conversation_state_with_messages(self):
        """Test conversation state with messages"""
        messages = [
            {"role": "assistant", "content": "Hello"},
            {"role": "워렌 버핏", "content": "투자에 대해 이야기해봅시다"}
        ]

        state = ConversationState(
            topic="투자 전략",
            messages=messages,
            input_tokens=100,
            output_tokens=200,
            cost=0.6
        )

        assert len(state.messages) == 2
        assert state.input_tokens == 100
        assert state.output_tokens == 200
        assert state.cost == 0.6


class TestEvaluateConversation:
    """Tests for conversation evaluation"""

    def test_evaluate_conversation_insufficient_messages(self):
        """Test with insufficient messages"""
        state = ConversationState(
            topic="Test",
            messages=[
                {"role": "test", "content": "message 1"},
                {"role": "test", "content": "message 2"}
            ]
        )

        assert evaluate_conversation(state) == False

    def test_evaluate_conversation_sufficient_messages(self):
        """Test with sufficient messages"""
        messages = [
            {"role": "test", "content": f"message {i}"}
            for i in range(5)
        ]

        state = ConversationState(topic="Test", messages=messages)
        assert evaluate_conversation(state) == True

    def test_evaluate_conversation_high_cost(self):
        """Test with high cost threshold"""
        state = ConversationState(
            topic="Test",
            messages=[{"role": "test", "content": "message"}],
            cost=51.0
        )

        assert evaluate_conversation(state) == True

    def test_evaluate_conversation_at_cost_threshold(self):
        """Test at exact cost threshold"""
        state = ConversationState(
            topic="Test",
            messages=[{"role": "test", "content": "message"}],
            cost=50.0
        )

        assert evaluate_conversation(state) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
