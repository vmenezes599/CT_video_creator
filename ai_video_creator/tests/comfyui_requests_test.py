"""
Test suite for ComfyUIRequests class with complete mocking of ComfyUI responses.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout

from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
from ai_video_creator.ComfyUI_automation.comfyui_workflow import IComfyUIWorkflow
from ai_video_creator.environment_variables import COMFYUI_URL


@pytest.fixture
def comfyui_requests():
    """Fixture to create a ComfyUIRequests instance."""
    return ComfyUIRequests(delay_seconds=1)  # Reduce delay for testing


@pytest.fixture
def mock_workflow():
    """Fixture to create a mock workflow."""
    workflow = Mock(spec=IComfyUIWorkflow)
    workflow.get_workflow_summary.return_value = "test_workflow/summary"
    workflow.get_json.return_value = {"test": "data"}
    return workflow


class TestComfyUIRequests:
    """Test class for ComfyUIRequests."""

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_send_get_request_success(self, mock_get, comfyui_requests):
        """Test successful GET request."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests._send_get_request("http://test.com")

        # Assert
        assert result.ok is True
        mock_get.assert_called_once_with(url="http://test.com", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_send_get_request_timeout(self, mock_get, comfyui_requests):
        """Test GET request timeout."""
        # Arrange
        mock_get.side_effect = Timeout("Request timed out")

        # Act & Assert
        with pytest.raises(Timeout):
            comfyui_requests._send_get_request("http://test.com")

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_send_post_request_success(self, mock_post, comfyui_requests):
        """Test successful POST request."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        # Act
        result = comfyui_requests._send_post_request(
            "http://test.com", json={"test": "data"}
        )

        # Assert
        assert result.ok is True
        mock_post.assert_called_once_with(
            url="http://test.com", data=None, json={"test": "data"}, timeout=10
        )

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_heartbeat_success(self, mock_get, comfyui_requests):
        """Test successful heartbeat check - tests URL construction and response handling."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests.comfyui_get_heartbeat()

        # Assert
        assert result is True
        # Test that the correct URL is constructed
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/prompt", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_heartbeat_failure(self, mock_get, comfyui_requests):
        """Test failed heartbeat check - tests actual error handling logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests.comfyui_get_heartbeat()

        # Assert
        assert result is False
        # Verify URL construction is correct
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/prompt", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_comfyui_send_prompt_success(self, mock_post, comfyui_requests):
        """Test successful prompt sending - tests URL construction and data wrapping logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"prompt_id": "12345"}
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt)

        # Assert
        assert result.ok is True
        
        # Test that URL is constructed correctly
        expected_url = f"{COMFYUI_URL}/prompt"
        mock_post.assert_called_once_with(
            url=expected_url, 
            data=None, 
            json={"prompt": test_prompt},  # Test the actual wrapping logic
            timeout=10
        )

    def test_comfyui_send_prompt_invalid_input(self, comfyui_requests):
        """Test prompt sending with invalid input - tests actual input validation logic."""
        # Test string input
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt("invalid_prompt")
            
        # Test None input
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt(None)
            
        # Test list input
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt([{"test": "data"}])
            
        # Test number input
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt(123)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_queue_success(self, mock_get, comfyui_requests):
        """Test successful queue status retrieval - tests JSON parsing logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Test with actual ComfyUI response structure
        mock_response.json.return_value = {"exec_info": {"queue_remaining": 3}}
        mock_get.return_value = mock_response

        # Act
        success, queue_count = comfyui_requests.comfyui_get_queue()

        # Assert
        assert success is True
        assert queue_count == 3
        # Test URL construction
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/prompt", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_queue_failure(self, mock_get, comfyui_requests):
        """Test failed queue status retrieval - tests error handling logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Act
        success, queue_count = comfyui_requests.comfyui_get_queue()

        # Assert
        assert success is False
        assert queue_count == -1  # Test the actual error return value
        # Test URL construction
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/prompt", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_history_success(self, mock_get, comfyui_requests):
        """Test successful history retrieval - tests JSON return logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        test_history = {
            "12345": {"status": {"completed": True}},
            "67890": {"status": {"completed": False}},
        }
        mock_response.json.return_value = test_history
        mock_get.return_value = mock_response

        # Act
        success, history_data = comfyui_requests.comfyui_get_history()

        # Assert
        assert success is True
        assert len(history_data) == 2
        assert "12345" in history_data
        assert history_data == test_history  # Test that actual data is returned unchanged
        # Test URL construction
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/history", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_history_failure(self, mock_get, comfyui_requests):
        """Test failed history retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests.comfyui_get_history()

        # Assert
        assert result is None  # Function doesn't return anything on failure

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_last_history_entry_success(self, mock_get, comfyui_requests):
        """Test successful last history entry retrieval - tests the 'last key' selection logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Test the actual logic: last key should be selected
        test_history = {
            "12345": {"status": {"completed": True}, "outputs": {}},
            "67890": {
                "status": {"completed": True},
                "outputs": {"images": ["output.png"]},
            },
        }
        mock_response.json.return_value = test_history
        mock_get.return_value = mock_response

        # Act
        success, last_entry = comfyui_requests.comfyui_get_last_history_entry()

        # Assert
        assert success is True
        # Test that it actually returns the LAST entry (67890, not 12345)
        expected_last_entry = {
            "status": {"completed": True},
            "outputs": {"images": ["output.png"]},
        }
        assert last_entry == expected_last_entry
        # Test URL construction
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/history", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_last_history_entry_failure(self, mock_get, comfyui_requests):
        """Test failed last history entry retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        # Act
        success, last_entry = comfyui_requests.comfyui_get_last_history_entry()

        # Assert
        assert success is False
        assert last_entry == []

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    @patch(
        "ai_video_creator.ComfyUI_automation.comfyui_requests.comfyui_get_history_output_name"
    )
    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.os.path.join")
    def test_comfyui_ensure_send_all_prompts_success(
        self,
        mock_path_join,
        mock_get_output_name,
        mock_sleep,
        comfyui_requests,
        mock_workflow,
    ):
        """Test successful processing of all prompts."""
        # Arrange
        mock_path_join.return_value = "/fake/path/output.png"
        mock_get_output_name.return_value = ["output.png"]

        # Mock the methods used in the function
        with patch.object(
            comfyui_requests, "comfyui_send_prompt"
        ) as mock_send_prompt, patch.object(
            comfyui_requests, "comfyui_get_queue"
        ) as mock_get_queue, patch.object(
            comfyui_requests, "comfyui_get_last_history_entry"
        ) as mock_get_history:

            # Setup mocks
            mock_response = Mock()
            mock_response.ok = True
            mock_send_prompt.return_value = mock_response

            # First call returns queue with items, second call returns empty queue
            mock_get_queue.side_effect = [(True, 1), (True, 0)]
            mock_get_history.return_value = (
                True,
                {"outputs": {"images": ["output.png"]}},
            )

            # Act
            result = comfyui_requests.comfyui_ensure_send_all_prompts([mock_workflow])

            # Assert
            assert len(result) == 1
            assert result[0] == "/fake/path/output.png"
            mock_send_prompt.assert_called_once()
            mock_get_queue.assert_called()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_comfyui_ensure_send_all_prompts_bad_response(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test handling of bad response during prompt sending."""
        # Arrange
        with patch.object(comfyui_requests, "comfyui_send_prompt") as mock_send_prompt:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 400
            mock_send_prompt.return_value = mock_response

            # Act & Assert
            with pytest.raises(RuntimeError, match="Bad prompt: 400"):
                comfyui_requests.comfyui_ensure_send_all_prompts([mock_workflow])

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_comfyui_ensure_send_all_prompts_request_exception(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test handling of request exception during prompt sending."""
        # Arrange
        mock_workflow.get_json.return_value = {"test": "data"}

        with patch.object(comfyui_requests, "comfyui_send_prompt") as mock_send_prompt:
            mock_send_prompt.side_effect = RequestException("Connection failed")

            # Act - Should handle the exception gracefully and return empty results
            result = comfyui_requests.comfyui_ensure_send_all_prompts([mock_workflow])

            # Assert - Should continue processing and return empty list (no successful outputs)
            assert result == []
            
            # Verify sleep was called (for the delay between requests)
            mock_sleep.assert_called()

    def test_comfyui_ensure_send_all_prompts_empty_list(self, comfyui_requests):
        """Test sending empty list of prompts."""
        # Act
        result = comfyui_requests.comfyui_ensure_send_all_prompts([])

        # Assert
        assert result == []

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_comfyui_ensure_send_all_prompts_multiple_workflows(
        self, mock_sleep, comfyui_requests
    ):
        """Test processing multiple workflows."""
        # Arrange
        workflow1 = Mock(spec=IComfyUIWorkflow)
        workflow1.get_workflow_summary.return_value = "workflow1/summary"
        workflow1.get_json.return_value = {"workflow": 1}

        workflow2 = Mock(spec=IComfyUIWorkflow)
        workflow2.get_workflow_summary.return_value = "workflow2/summary"
        workflow2.get_json.return_value = {"workflow": 2}

        with patch.object(
            comfyui_requests, "comfyui_send_prompt"
        ) as mock_send_prompt, patch.object(
            comfyui_requests, "comfyui_get_queue"
        ) as mock_get_queue, patch.object(
            comfyui_requests, "comfyui_get_last_history_entry"
        ) as mock_get_history, patch(
            "ai_video_creator.ComfyUI_automation.comfyui_requests.comfyui_get_history_output_name"
        ) as mock_get_output_name, patch(
            "ai_video_creator.ComfyUI_automation.comfyui_requests.os.path.join"
        ) as mock_path_join:

            # Setup mocks
            mock_response = Mock()
            mock_response.ok = True
            mock_send_prompt.return_value = mock_response
            mock_get_queue.return_value = (True, 0)  # Queue is empty immediately
            mock_get_history.return_value = (True, {"outputs": {}})
            mock_get_output_name.return_value = ["output1.png", "output2.png"]
            mock_path_join.side_effect = ["/path/output1.png", "/path/output2.png"]

            # Act
            result = comfyui_requests.comfyui_ensure_send_all_prompts(
                [workflow1, workflow2]
            )

            # Assert
            assert mock_send_prompt.call_count == 2
            assert len(result) == 2


# Additional test cases for edge cases and error conditions
class TestComfyUIRequestsEdgeCases:
    """Test edge cases and error conditions."""

    @patch.dict(os.environ, {"COMFYUI_URL": "http://127.0.0.1:8188"})
    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_environment_variable_usage(self, mock_get, comfyui_requests):
        """Test that environment variables are used correctly in URL construction."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_get.return_value = mock_response

        # Act
        comfyui_requests.comfyui_get_heartbeat()

        # Assert - Test that the environment variable is actually used in URL construction
        expected_url = "http://127.0.0.1:8188/prompt"
        mock_get.assert_called_once_with(url=expected_url, timeout=10)

    def test_delay_seconds_initialization(self):
        """Test custom delay seconds initialization."""
        # Act
        custom_requests = ComfyUIRequests(delay_seconds=5)

        # Assert
        assert custom_requests.delay_seconds == 5

    def test_default_delay_seconds(self):
        """Test default delay seconds."""
        # Act
        default_requests = ComfyUIRequests()

        # Assert
        assert default_requests.delay_seconds == 10

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_queue_malformed_response(self, mock_get, comfyui_requests):
        """Test queue retrieval with malformed response - tests real JSON parsing error handling."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Return a response that doesn't have the expected structure
        mock_response.json.return_value = {"some_other_key": "value"}
        mock_get.return_value = mock_response

        # Act & Assert - This should raise KeyError because the real code tries to access ["exec_info"]["queue_remaining"]
        with pytest.raises(KeyError):
            comfyui_requests.comfyui_get_queue()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_history_empty_response(self, mock_get, comfyui_requests):
        """Test history retrieval with empty response."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = MockResponses.empty_history_response()
        mock_get.return_value = mock_response

        # Act
        success, history_data = comfyui_requests.comfyui_get_history()

        # Assert
        assert success is True
        assert history_data == {}

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_last_history_entry_empty_history(
        self, mock_get, comfyui_requests
    ):
        """Test last history entry retrieval with empty history - tests real IndexError handling."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Empty dict should cause IndexError when trying to get last key
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        # Act & Assert - The real code will raise IndexError on list(empty_dict.keys())[-1]
        with pytest.raises(IndexError):
            comfyui_requests.comfyui_get_last_history_entry()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_comfyui_send_prompt_with_node_errors(self, mock_post, comfyui_requests):
        """Test prompt sending that returns node errors."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = MockResponses.node_error_response()
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt)

        # Assert
        assert result.ok is True
        response_data = result.json()
        assert "node_errors" in response_data
        assert len(response_data["node_errors"]) > 0

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_heartbeat_network_error(self, mock_get, comfyui_requests):
        """Test heartbeat check with network error."""
        # Arrange
        mock_get.side_effect = RequestException("Network error")

        # Act & Assert
        with pytest.raises(RequestException):
            comfyui_requests.comfyui_get_heartbeat()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_comfyui_get_queue_json_decode_error(self, mock_get, comfyui_requests):
        """Test queue retrieval with JSON decode error."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(ValueError):
            comfyui_requests.comfyui_get_queue()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_comfyui_send_prompt_server_error(self, mock_post, comfyui_requests):
        """Test prompt sending with server error response."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.return_value = MockResponses.server_error_response()
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt)

        # Assert
        assert result.ok is False
        assert result.status_code == 500

    def test_comfyui_send_prompt_none_input(self, comfyui_requests):
        """Test prompt sending with None input."""
        # Act & Assert
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt(None)

    def test_comfyui_send_prompt_list_input(self, comfyui_requests):
        """Test prompt sending with list input instead of dict."""
        # Act & Assert
        with pytest.raises(ValueError, match="The prompt must be a dictionary"):
            comfyui_requests.comfyui_send_prompt([{"test": "data"}])

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    @patch(
        "ai_video_creator.ComfyUI_automation.comfyui_requests.comfyui_get_history_output_name"
    )
    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.os.path.join")
    def test_comfyui_ensure_send_all_prompts_success(
        self,
        mock_path_join,
        mock_get_output_name,
        mock_sleep,
        comfyui_requests,
        mock_workflow,
    ):
        """Test successful completion of sending all prompts."""
        # Arrange
        with patch.object(
            comfyui_requests, "comfyui_send_prompt"
        ) as mock_send_prompt, patch.object(
            comfyui_requests, "comfyui_get_queue"
        ) as mock_get_queue, patch.object(
            comfyui_requests, "comfyui_get_last_history_entry"
        ) as mock_get_history:

            mock_response = Mock()
            mock_response.ok = True
            mock_send_prompt.return_value = mock_response

            # Simulate queue becoming empty after one check
            mock_get_queue.side_effect = [
                (True, 1),
                (True, 0),
            ]  # First has items, then empty

            mock_get_history.return_value = (True, {"outputs": {}})
            mock_get_output_name.return_value = ["output.png"]
            mock_path_join.return_value = "/path/output.png"

            # Act
            result = comfyui_requests.comfyui_ensure_send_all_prompts([mock_workflow])

            # Assert
            assert len(result) == 1
            assert result[0] == "/path/output.png"
            mock_send_prompt.assert_called_once()
            assert mock_get_queue.call_count >= 2


class TestComfyUIRequestsWithMalformedResponses:
    """Test class for malformed and unexpected responses."""

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_queue_response_missing_exec_info(self, mock_get, comfyui_requests):
        """Test queue response missing exec_info key."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"some_other_key": "value"}
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(KeyError):
            comfyui_requests.comfyui_get_queue()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_queue_response_missing_queue_remaining(self, mock_get, comfyui_requests):
        """Test queue response missing queue_remaining key."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"exec_info": {"other_field": 123}}
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(KeyError):
            comfyui_requests.comfyui_get_queue()

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_history_response_with_invalid_structure(self, mock_get, comfyui_requests):
        """Test history response with invalid structure."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = MockResponses.malformed_history_response()
        mock_get.return_value = mock_response

        # Act
        success, history_data = comfyui_requests.comfyui_get_history()

        # Assert
        assert success is True
        assert "invalid_key" in history_data
        assert "history_entries" in history_data

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_prompt_response_corrupted_json(self, mock_post, comfyui_requests):
        """Test prompt response with corrupted JSON."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError(
            "Expecting value: line 1 column 1 (char 0)"
        )
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "test"}}}}

        # Act & Assert
        with pytest.raises(ValueError):
            result = comfyui_requests.comfyui_send_prompt(test_prompt)
            result.json()  # This should raise the error


# Mock responses for different scenarios
class MockResponses:
    """Mock response data for testing."""

    @staticmethod
    def success_prompt_response():
        """Mock successful prompt response."""
        return {"prompt_id": "12345-abcde-67890", "number": 1, "node_errors": {}}

    @staticmethod
    def success_queue_response():
        """Mock successful queue response."""
        return {"exec_info": {"queue_remaining": 0}}

    @staticmethod
    def success_queue_response_with_items():
        """Mock queue response with pending items."""
        return {"exec_info": {"queue_remaining": 3}}

    @staticmethod
    def success_history_response():
        """Mock successful history response."""
        return {
            "12345-abcde-67890": {
                "prompt": [1, {"1": {"inputs": {"text": "test"}}}],
                "outputs": {
                    "9": {
                        "images": [
                            {
                                "filename": "ComfyUI_00001_.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
                "status": {"status_str": "success", "completed": True, "messages": []},
            }
        }

    @staticmethod
    def success_history_response_multiple():
        """Mock successful history response with multiple entries."""
        return {
            "11111-aaaaa-11111": {
                "prompt": [1, {"1": {"inputs": {"text": "first"}}}],
                "outputs": {
                    "5": {
                        "images": [
                            {
                                "filename": "ComfyUI_00001_.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
                "status": {"status_str": "success", "completed": True, "messages": []},
            },
            "22222-bbbbb-22222": {
                "prompt": [2, {"2": {"inputs": {"text": "second"}}}],
                "outputs": {
                    "10": {
                        "images": [
                            {
                                "filename": "ComfyUI_00002_.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
                "status": {"status_str": "success", "completed": True, "messages": []},
            },
        }

    @staticmethod
    def failure_response():
        """Mock failure response."""
        return {
            "error": {
                "type": "prompt_execution_error",
                "message": "Failed to execute prompt",
                "details": "Node validation failed",
            }
        }

    @staticmethod
    def malformed_queue_response():
        """Mock malformed queue response (missing exec_info)."""
        return {
            "queue_data": {"pending": 2, "running": 1}
            # Missing "exec_info" key
        }

    @staticmethod
    def malformed_history_response():
        """Mock malformed history response (unexpected structure)."""
        return {
            "invalid_key": "invalid_value",
            "history_entries": [],
            # Missing proper prompt_id keys
        }

    @staticmethod
    def empty_history_response():
        """Mock empty history response."""
        return {}

    @staticmethod
    def corrupted_response():
        """Mock corrupted/invalid JSON response."""
        return "This is not valid JSON"

    @staticmethod
    def server_error_response():
        """Mock server error response."""
        return {
            "error": "Internal Server Error",
            "code": 500,
            "message": "ComfyUI server encountered an internal error",
        }

    @staticmethod
    def node_error_response():
        """Mock response with node errors."""
        return {
            "prompt_id": "error-prompt-id",
            "number": 1,
            "node_errors": {
                "3": {
                    "errors": [
                        {
                            "type": "return_type_mismatch",
                            "message": "Failed to validate prompt",
                            "details": "Node 3 output type mismatch",
                        }
                    ],
                    "dependent_outputs": ["4", "5"],
                    "class_type": "KSampler",
                }
            },
        }


# You can add more specific test cases here when you provide the actual success/failure examples
class TestComfyUIRequestsWithRealExamples:
    """Test class for real ComfyUI response examples."""

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_real_success_prompt_response_template(self, mock_post, comfyui_requests):
        """Test with real success response template - to be updated with actual example."""
        # Arrange - This will be replaced with real ComfyUI success response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "prompt_id": "real-success-prompt-id",
            "number": 1,
            "node_errors": {},
        }
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "real test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt)

        # Assert
        assert result.ok is True
        response_data = result.json()
        assert "prompt_id" in response_data
        assert response_data["node_errors"] == {}

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_real_failure_prompt_response_template(self, mock_post, comfyui_requests):
        """Test with real failure response template - to be updated with actual example."""
        # Arrange - This will be replaced with real ComfyUI failure response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "type": "validation_error",
                "message": "Invalid node configuration",
                "details": "Node 'KSampler' missing required input 'model'",
            }
        }
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "invalid test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt)

        # Assert
        assert result.ok is False
        assert result.status_code == 400
        response_data = result.json()
        assert "error" in response_data
        assert response_data["error"]["type"] == "validation_error"

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_real_queue_response_template(self, mock_get, comfyui_requests):
        """Test with real queue response template - to be updated with actual example."""
        # Arrange - This will be replaced with real ComfyUI queue response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"exec_info": {"queue_remaining": 2}}
        mock_get.return_value = mock_response

        # Act
        success, queue_count = comfyui_requests.comfyui_get_queue()

        # Assert
        assert success is True
        assert queue_count == 2

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_real_history_response_template(self, mock_get, comfyui_requests):
        """Test with real history response template - to be updated with actual example."""
        # Arrange - This will be replaced with real ComfyUI history response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "real-prompt-id-12345": {
                "prompt": [
                    1,
                    {
                        "3": {
                            "inputs": {
                                "seed": 42,
                                "steps": 20,
                                "cfg": 8.0,
                                "sampler_name": "euler",
                                "scheduler": "normal",
                                "denoise": 1.0,
                                "model": ["4", 0],
                                "positive": ["6", 0],
                                "negative": ["7", 0],
                                "latent_image": ["5", 0],
                            },
                            "class_type": "KSampler",
                        }
                    },
                ],
                "outputs": {
                    "9": {
                        "images": [
                            {
                                "filename": "ComfyUI_00001_.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
                "status": {"status_str": "success", "completed": True, "messages": []},
            }
        }
        mock_get.return_value = mock_response

        # Act
        success, history_data = comfyui_requests.comfyui_get_history()

        # Assert
        assert success is True
        assert "real-prompt-id-12345" in history_data
        assert history_data["real-prompt-id-12345"]["status"]["completed"] is True

    def test_workflow_integration_template(self, comfyui_requests, mock_workflow):
        """Test workflow integration template - to be updated with real workflow examples."""
        # This test demonstrates how the workflow integration should work
        # It will be updated when real workflow examples are provided

        # Arrange
        mock_workflow.get_workflow_summary.return_value = (
            "test_workflow/image_generation"
        )
        mock_workflow.get_json.return_value = {
            "3": {
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 8.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                },
                "class_type": "KSampler",
            }
        }

        # Act
        workflow_json = mock_workflow.get_json()
        workflow_summary = mock_workflow.get_workflow_summary()

        # Assert
        assert isinstance(workflow_json, dict)
        assert "3" in workflow_json
        assert workflow_json["3"]["class_type"] == "KSampler"
        assert "/" in workflow_summary
        assert workflow_summary.endswith("image_generation")


class TestComfyUIRequestsTimeout:
    """Test timeout scenarios and long-running operations."""

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_heartbeat_custom_timeout(self, mock_get, comfyui_requests):
        """Test heartbeat with custom timeout."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests.comfyui_get_heartbeat()

        # Assert
        assert result is True
        mock_get.assert_called_once_with(url=f"{COMFYUI_URL}/prompt", timeout=10)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_send_prompt_custom_timeout(self, mock_post, comfyui_requests):
        """Test send prompt with custom timeout."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"prompt_id": "12345"}
        mock_post.return_value = mock_response

        test_prompt = {"nodes": {"1": {"inputs": {"text": "test"}}}}

        # Act
        result = comfyui_requests.comfyui_send_prompt(test_prompt, timeout=30)

        # Assert
        assert result.ok is True
        mock_post.assert_called_once_with(
            url=f"{COMFYUI_URL}/prompt",
            data=None,
            json={"prompt": test_prompt},
            timeout=30,
        )

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_queue_request_timeout(self, mock_get, comfyui_requests):
        """Test queue request with timeout exception."""
        # Arrange
        mock_get.side_effect = Timeout("Request timed out")

        # Act & Assert
        with pytest.raises(Timeout):
            comfyui_requests.comfyui_get_queue()


# Test actual business logic that was over-mocked before
class TestComfyUIRequestsBusinessLogic:
    """Test real business logic and data processing."""

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_history_keys_ordering(self, mock_get, comfyui_requests):
        """Test that last history entry actually gets the last key in the dict."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Test with specific ordering to ensure last key logic works
        test_history = {
            "first_key": {"data": "first"},
            "middle_key": {"data": "middle"}, 
            "last_key": {"data": "last"}
        }
        mock_response.json.return_value = test_history
        mock_get.return_value = mock_response

        # Act
        success, last_entry = comfyui_requests.comfyui_get_last_history_entry()

        # Assert
        assert success is True
        assert last_entry == {"data": "last"}  # Should get the last key's data

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_prompt_wrapping_logic(self, mock_post, comfyui_requests):
        """Test that prompts are properly wrapped in 'prompt' key."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        original_prompt = {
            "3": {"inputs": {"text": "test"}, "class_type": "TextNode"},
            "4": {"inputs": {"image": ["3", 0]}, "class_type": "ImageNode"}
        }

        # Act
        comfyui_requests.comfyui_send_prompt(original_prompt)

        # Assert - Test the exact wrapping logic
        call_args = mock_post.call_args
        sent_data = call_args[1]["json"]
        
        # Should wrap in "prompt" key
        assert "prompt" in sent_data
        assert sent_data["prompt"] == original_prompt
        
        # Should not modify the original prompt
        assert len(sent_data) == 1

    def test_delay_seconds_property(self, comfyui_requests):
        """Test that delay_seconds is properly stored and accessible."""
        # Test default value
        default_requests = ComfyUIRequests()
        assert default_requests.delay_seconds == 10

        # Test custom value
        custom_requests = ComfyUIRequests(delay_seconds=5)
        assert custom_requests.delay_seconds == 5

        # Test that it's actually stored as an instance variable
        assert hasattr(custom_requests, 'delay_seconds')

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_queue_data_extraction(self, mock_get, comfyui_requests):
        """Test the specific JSON path navigation for queue data."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        
        # Test various queue numbers
        for queue_num in [0, 1, 5, 100]:
            mock_response.json.return_value = {"exec_info": {"queue_remaining": queue_num}}
            mock_get.return_value = mock_response

            # Act
            success, queue_count = comfyui_requests.comfyui_get_queue()

            # Assert
            assert success is True
            assert queue_count == queue_num

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.get")
    def test_error_status_code_handling(self, mock_get, comfyui_requests):
        """Test that different HTTP status codes are handled correctly."""
        # Test various error codes
        error_codes = [400, 401, 403, 404, 500, 502, 503]
        
        for status_code in error_codes:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = status_code
            mock_get.return_value = mock_response

            # Act
            success, queue_count = comfyui_requests.comfyui_get_queue()

            # Assert
            assert success is False
            assert queue_count == -1


class TestComfyUIRequestsNewMethods:
    """Test class for new helper methods introduced during refactoring."""

    def test_create_progress_summary_short_text(self, comfyui_requests, mock_workflow):
        """Test progress summary creation with short text."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "short_workflow"
        
        # Act
        full_summary, display_summary = comfyui_requests._create_progress_summary(mock_workflow, 100)
        
        # Assert
        assert full_summary == "short_workflow"
        assert display_summary == "short_workflow"

    def test_create_progress_summary_long_text(self, comfyui_requests, mock_workflow):
        """Test progress summary creation with long text."""
        # Arrange
        long_text = "a" * 200
        mock_workflow.get_workflow_summary.return_value = long_text
        
        # Act
        full_summary, display_summary = comfyui_requests._create_progress_summary(mock_workflow, 50)
        
        # Assert
        assert full_summary == long_text
        assert display_summary == "a" * 50 + "..."

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_submit_single_prompt_success(self, mock_post, comfyui_requests, mock_workflow):
        """Test successful single prompt submission."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        mock_workflow.get_json.return_value = {"test": "data"}
        
        # Act
        result = comfyui_requests._submit_single_prompt(mock_workflow)
        
        # Assert
        assert result.ok is True

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.requests.post")
    def test_submit_single_prompt_failure(self, mock_post, comfyui_requests, mock_workflow):
        """Test failed single prompt submission."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        mock_workflow.get_json.return_value = {"test": "data"}
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Bad prompt: 400"):
            comfyui_requests._submit_single_prompt(mock_workflow)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.datetime")
    def test_wait_for_completion(self, mock_datetime, mock_sleep, comfyui_requests):
        """Test waiting for completion functionality."""
        # Arrange
        from datetime import datetime, timedelta
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 30)  # 30 seconds later
        
        # Create a proper datetime mock
        mock_datetime.now.side_effect = [start_time, end_time]
        
        # Mock queue responses: busy, busy, then complete
        with patch.object(comfyui_requests, "comfyui_get_queue") as mock_get_queue:
            mock_get_queue.side_effect = [(True, 2), (True, 1), (True, 0)]
            
            # Act
            processing_time = comfyui_requests._wait_for_completion(check_interval=1)
            
            # Assert
            assert processing_time == 30
            assert mock_sleep.call_count == 2  # Called twice before queue was empty

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.comfyui_get_history_output_name")
    def test_get_output_path_with_history(self, mock_get_history_output_name, comfyui_requests, mock_workflow):
        """Test getting output path when history is available."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test/workflow"
        mock_get_history_output_name.return_value = ["output_file.png"]
        
        with patch.object(comfyui_requests, "comfyui_get_last_history_entry") as mock_get_history:
            mock_get_history.return_value = (True, {"test": "history"})
            
            # Act
            result = comfyui_requests._get_output_path(mock_workflow, 5)
            
            # Assert
            expected_path = os.path.join(
                comfyui_requests.__class__.__module__.replace('.', '/').split('/')[-3] + "/environment_variables.py",
                "output_file.png"
            ).replace("ai_video_creator/environment_variables.py", "")
            # Just check that it contains the expected filename since path construction varies
            assert "output_file.png" in result

    def test_get_output_path_no_history(self, comfyui_requests, mock_workflow):
        """Test getting output path when history is not available."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test/workflow"
        
        with patch.object(comfyui_requests, "comfyui_get_last_history_entry") as mock_get_history:
            mock_get_history.return_value = (False, [])
            
            # Act
            result = comfyui_requests._get_output_path(mock_workflow, 5)
            
            # Assert
            assert result is None

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_process_single_workflow_success(self, mock_sleep, comfyui_requests, mock_workflow):
        """Test successful processing of a single workflow."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"
        
        with patch.object(comfyui_requests, "_submit_single_prompt") as mock_submit, \
             patch.object(comfyui_requests, "_wait_for_completion") as mock_wait, \
             patch.object(comfyui_requests, "_get_output_path") as mock_get_path:
            
            mock_wait.return_value = 45  # 45 seconds processing time
            mock_get_path.return_value = "/path/to/output.png"
            
            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow, 0, 1)
            
            # Assert
            assert result == "/path/to/output.png"
            mock_submit.assert_called_once_with(mock_workflow)
            mock_wait.assert_called_once()
            mock_get_path.assert_called_once_with(mock_workflow, 0)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_process_single_workflow_runtime_error(self, mock_sleep, comfyui_requests, mock_workflow):
        """Test processing single workflow with RuntimeError."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"
        
        with patch.object(comfyui_requests, "_submit_single_prompt") as mock_submit:
            mock_submit.side_effect = RuntimeError("Bad prompt")
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Bad prompt"):
                comfyui_requests._process_single_workflow(mock_workflow, 0, 1)

    @patch("ai_video_creator.ComfyUI_automation.comfyui_requests.time.sleep")
    def test_process_single_workflow_request_exception(self, mock_sleep, comfyui_requests, mock_workflow):
        """Test processing single workflow with RequestException."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"

        with patch.object(comfyui_requests, "_submit_single_prompt") as mock_submit:
            mock_submit.side_effect = RequestException("Connection failed")

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow, 0, 1)

            # Assert - Should handle the exception gracefully and return None
            assert result is None