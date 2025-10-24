"""
Test suite for ComfyUIRequests class with complete mocking of ComfyUI responses.
"""

from unittest.mock import Mock, patch

import pytest
from requests.exceptions import RequestException

from ai_video_creator.comfyui import ComfyUIRequests
from ai_video_creator.comfyui.comfyui_workflow import IComfyUIWorkflow


@pytest.fixture
def comfyui_requests():
    """Fixture to create a ComfyUIRequests instance."""
    return ComfyUIRequests(
        max_retries_per_request=3, delay_seconds=1
    )  # Reduce delay for testing


@pytest.fixture
def mock_workflow():
    """Fixture to create a mock workflow."""
    workflow = Mock(spec=IComfyUIWorkflow)
    workflow.get_workflow_summary.return_value = "test_workflow/summary"
    workflow.get_json.return_value = {"test": "data"}
    return workflow


class TestComfyUIRequests:
    """Test class for ComfyUIRequests."""

    @patch("ai_video_creator.comfyui.comfyui_requests.requests.post")
    def test_comfyui_send_prompt_success(self, mock_post, comfyui_requests):
        """Test successful prompt sending with proper data wrapping."""
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

    @patch("ai_video_creator.comfyui.comfyui_requests.requests.get")
    def test_comfyui_get_processing_queue_success(self, mock_get, comfyui_requests):
        """Test successful queue status retrieval - tests JSON parsing logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        # Test with actual ComfyUI response structure
        mock_response.json.return_value = {"exec_info": {"queue_remaining": 3}}
        mock_get.return_value = mock_response

        # Act
        queue_count = comfyui_requests.get_processing_queue()

        # Assert
        assert queue_count == 3

    @patch("ai_video_creator.comfyui.comfyui_requests.requests.get")
    def test_comfyui_get_processing_queue_failure(self, mock_get, comfyui_requests):
        """Test failed queue status retrieval - tests error handling logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Act
        queue_count = comfyui_requests.get_processing_queue()

        # Assert
        assert queue_count == -1

    @patch("ai_video_creator.comfyui.comfyui_requests.requests.get")
    def test_comfyui_get_history_success(self, mock_get, comfyui_requests):
        """Test successful history retrieval - tests JSON return logic."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = True
        test_history = {
            "12345": {"status": {"status_str": "success", "completed": True}},
            "67890": {"status": {"status_str": "error", "completed": False}},
        }
        mock_response.json.return_value = test_history
        mock_get.return_value = mock_response

        # Act
        history_data = comfyui_requests.get_history()

        # Assert
        assert len(history_data) == 2
        assert "12345" in history_data
        assert history_data == test_history

    @patch("ai_video_creator.comfyui.comfyui_requests.requests.get")
    def test_comfyui_get_history_failure(self, mock_get, comfyui_requests):
        """Test failed history retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act
        result = comfyui_requests.get_history()

        # Assert
        assert result == {}  # Function returns empty dict on failure

    def test_get_last_history_entry_success(self, comfyui_requests):
        """Test successful last history entry retrieval - tests the 'last key' selection logic."""
        # Arrange
        test_history = {
            "12345": {
                "status": {"status_str": "success", "completed": True},
                "outputs": {},
            },
            "67890": {
                "status": {"status_str": "success", "completed": True},
                "outputs": {"images": ["output.png"]},
            },
        }

        with patch.object(comfyui_requests, "get_history") as mock_get_history:
            mock_get_history.return_value = test_history

            # Act
            last_entry = comfyui_requests.get_last_history_entry()

            # Assert
            # Test that it actually returns the LAST entry (67890, not 12345)
            expected_last_entry = {
                "status": {"status_str": "success", "completed": True},
                "outputs": {"images": ["output.png"]},
            }
            assert last_entry == expected_last_entry

    def test_get_last_history_entry_failure(self, comfyui_requests):
        """Test failed last history entry retrieval."""
        # Arrange
        with patch.object(comfyui_requests, "get_history") as mock_get_history:
            mock_get_history.return_value = {}

            # Act
            last_entry = comfyui_requests.get_last_history_entry()

            # Assert
            assert last_entry == {}

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_comfyui_ensure_send_all_prompts_filters_none_results(
        self, mock_sleep, comfyui_requests, tmp_path
    ):
        """Test that ensure_send_all_prompts properly filters out None results and maintains list integrity."""
        # Arrange
        workflow1 = Mock(spec=IComfyUIWorkflow)
        workflow1.get_workflow_summary.return_value = "workflow1/summary"

        workflow2 = Mock(spec=IComfyUIWorkflow)
        workflow2.get_workflow_summary.return_value = "workflow2/summary"

        workflow3 = Mock(spec=IComfyUIWorkflow)
        workflow3.get_workflow_summary.return_value = "workflow3/summary"

        with patch.object(
            comfyui_requests, "_process_single_workflow"
        ) as mock_process_workflow, patch.object(
            comfyui_requests, "download_all_files"
        ) as mock_download:
            # Simulate: success, failure, success
            mock_process_workflow.side_effect = [
                ["/path/output1.png"],
                [],  # Empty list instead of None for failure
                ["/path/output3.png"],
            ]
            mock_download.return_value = ["/path/output1.png", "/path/output3.png"]

            # Act
            result = comfyui_requests.ensure_send_all_prompts(
                [workflow1, workflow2, workflow3], tmp_path
            )

            # Assert - Should only contain successful outputs
            assert len(result) == 2  # Only non-None results
            assert result == ["/path/output1.png", "/path/output3.png"]
            assert mock_process_workflow.call_count == 3
            assert mock_sleep.call_count == 3

    def test_comfyui_ensure_send_all_prompts_empty_list(
        self, comfyui_requests, tmp_path
    ):
        """Test sending empty list of prompts."""
        with patch.object(comfyui_requests, "download_all_files") as mock_download:
            mock_download.return_value = []

            # Act
            result = comfyui_requests.ensure_send_all_prompts([], tmp_path)

            # Assert
            assert result == []

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    @patch("ai_video_creator.comfyui.comfyui_requests.datetime")
    def test_wait_for_completion_success(
        self, mock_datetime, mock_sleep, comfyui_requests
    ):
        """Test successful completion waiting - tests polling logic and timing calculation."""
        # Arrange
        prompt_id = "test_prompt_123"
        start_time = Mock()
        end_time = Mock()

        # Mock timedelta behavior for (end_time - start_time).seconds
        time_diff = Mock()
        time_diff.seconds = 15
        end_time.__sub__ = Mock(return_value=time_diff)

        # Mock datetime behavior
        mock_datetime.now.side_effect = [start_time, end_time]

        # Mock history responses - first call empty, second call has our prompt
        with patch.object(comfyui_requests, "get_history") as mock_get_history:
            mock_get_history.side_effect = [
                {},  # First call - prompt not ready yet
                {prompt_id: {"status": "completed"}},  # Second call - prompt found
            ]

            # Act
            processing_time = comfyui_requests._wait_for_completion(prompt_id)

            # Assert
            assert processing_time == 15
            assert mock_get_history.call_count == 2
            assert mock_sleep.call_count == 1
            mock_sleep.assert_called_with(1)  # Default check_interval

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    @patch("ai_video_creator.comfyui.comfyui_requests.datetime")
    def test_wait_for_completion_custom_interval(
        self, mock_datetime, mock_sleep, comfyui_requests
    ):
        """Test completion waiting with custom check interval."""
        # Arrange
        prompt_id = "test_prompt_456"
        start_time = Mock()
        end_time = Mock()

        # Mock timedelta behavior
        time_diff = Mock()
        time_diff.seconds = 30
        end_time.__sub__ = Mock(return_value=time_diff)

        mock_datetime.now.side_effect = [start_time, end_time]

        with patch.object(comfyui_requests, "get_history") as mock_get_history:
            mock_get_history.side_effect = [
                {},
                {},
                {prompt_id: {"status": "completed"}},
            ]

            # Act
            processing_time = comfyui_requests._wait_for_completion(
                prompt_id, check_interval=3
            )

            # Assert
            assert processing_time == 30
            assert mock_get_history.call_count == 3
            assert mock_sleep.call_count == 2
            # Verify custom interval is used
            mock_sleep.assert_called_with(3)

    def test_check_for_output_success_valid_response(self, comfyui_requests):
        """Test output success validation with valid successful response."""
        # Arrange
        valid_response = {"status": {"status_str": "success", "completed": True}}

        # Act & Assert - Should not raise any exception
        comfyui_requests._check_for_output_success(valid_response)

    def test_check_for_output_success_failed_status(self, comfyui_requests):
        """Test output success validation with failed status - tests error propagation."""
        # Arrange
        failed_response = {"status": {"status_str": "error", "completed": True}}

        # Act & Assert
        with pytest.raises(RuntimeError, match="ComfyUI request failed: error"):
            comfyui_requests._check_for_output_success(failed_response)

    def test_check_for_output_success_incomplete_status(self, comfyui_requests):
        """Test output success validation with incomplete status - tests error propagation."""
        # Arrange
        incomplete_response = {"status": {"status_str": "success", "completed": False}}

        # Act & Assert
        with pytest.raises(RuntimeError, match="ComfyUI request failed: success"):
            comfyui_requests._check_for_output_success(incomplete_response)

    def test_check_for_output_success_both_failed_and_incomplete(
        self, comfyui_requests
    ):
        """Test output success validation with both failed status and incomplete - tests priority of error checking."""
        # Arrange
        failed_incomplete_response = {
            "status": {"status_str": "timeout", "completed": False}
        }

        # Act & Assert - Should fail on status_str first
        with pytest.raises(RuntimeError, match="ComfyUI request failed: timeout"):
            comfyui_requests._check_for_output_success(failed_incomplete_response)

    @patch.object(ComfyUIRequests, "_comfyui_get_history_output_name")
    @patch("ai_video_creator.comfyui.comfyui_requests.os.path.join")
    def test_get_output_path_success(
        self, mock_path_join, mock_get_output_name, comfyui_requests
    ):
        """Test successful output path construction - tests file path building logic."""
        # Arrange
        history_entry = {"outputs": {"images": ["file1.png", "file2.png"]}}
        mock_get_output_name.return_value = ["output_image.png", "backup_image.png"]
        mock_path_join.side_effect = [
            "/path/to/output/output_image.png",
            "/path/to/output/backup_image.png",
        ]

        # Act
        output_paths = comfyui_requests._get_output_paths(history_entry)

        # Assert
        assert output_paths == [
            "/path/to/output/output_image.png",
            "/path/to/output/backup_image.png",
        ]
        mock_get_output_name.assert_called_once_with(history_entry)
        # Verify it uses both output names and joins with COMFYUI_OUTPUT_FOLDER
        assert mock_path_join.call_count == 2

    @patch.object(ComfyUIRequests, "_comfyui_get_history_output_name")
    def test_get_output_path_no_outputs(self, mock_get_output_name, comfyui_requests):
        """Test output path when no outputs are found - tests empty list return behavior."""
        # Arrange
        history_entry = {"outputs": {}}
        mock_get_output_name.return_value = []  # No output names found

        # Act
        output_paths = comfyui_requests._get_output_paths(history_entry)

        # Assert
        assert output_paths == []
        mock_get_output_name.assert_called_once_with(history_entry)

    @patch.object(ComfyUIRequests, "_comfyui_get_history_output_name")
    def test_get_output_path_none_outputs(self, mock_get_output_name, comfyui_requests):
        """Test output path when helper returns None - tests empty list handling."""
        # Arrange
        history_entry = {"outputs": {"images": ["test.png"]}}
        mock_get_output_name.return_value = None

        # Act
        output_paths = comfyui_requests._get_output_paths(history_entry)

        # Assert
        assert output_paths == []

    def test_create_workflow_summary_short_summary(
        self, comfyui_requests, mock_workflow
    ):
        """Test workflow summary creation with short summary - tests no truncation."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "Short workflow name"

        # Act
        full_summary, display_summary = comfyui_requests._create_workflow_summary(
            mock_workflow
        )

        # Assert
        assert full_summary == "Short workflow name"
        assert display_summary == "Short workflow name"
        assert "..." not in display_summary

    def test_create_workflow_summary_long_summary(
        self, comfyui_requests, mock_workflow
    ):
        """Test workflow summary creation with long summary - tests truncation logic."""
        # Arrange
        long_name = "A" * 150  # 150 characters, should be truncated
        mock_workflow.get_workflow_summary.return_value = long_name

        # Act
        full_summary, display_summary = comfyui_requests._create_workflow_summary(
            mock_workflow
        )

        # Assert
        assert full_summary == long_name
        assert len(display_summary) == 103  # 100 + "..." = 103
        assert display_summary.endswith("...")
        assert display_summary.startswith("A" * 100)

    def test_create_workflow_summary_exactly_max_length(
        self, comfyui_requests, mock_workflow
    ):
        """Test workflow summary creation with exactly max length - tests boundary condition."""
        # Arrange
        exact_length_name = "B" * 100  # Exactly 100 characters
        mock_workflow.get_workflow_summary.return_value = exact_length_name

        # Act
        full_summary, display_summary = comfyui_requests._create_workflow_summary(
            mock_workflow
        )

        # Assert
        assert full_summary == exact_length_name
        assert display_summary == exact_length_name
        assert "..." not in display_summary

    def test_create_workflow_summary_custom_max_length(
        self, comfyui_requests, mock_workflow
    ):
        """Test workflow summary creation with custom max length."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = (
            "This is a longer workflow name"
        )

        # Act
        full_summary, display_summary = comfyui_requests._create_workflow_summary(
            mock_workflow, max_length=10
        )

        # Assert
        assert full_summary == "This is a longer workflow name"
        assert display_summary == "This is a ..."
        assert len(display_summary) == 13  # 10 + "..." = 13

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_process_single_workflow_success(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test successful single workflow processing - tests complete flow integration."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"

        with patch.object(
            comfyui_requests, "_submit_single_prompt"
        ) as mock_submit, patch.object(
            comfyui_requests, "_wait_for_completion"
        ) as mock_wait, patch.object(
            comfyui_requests, "get_last_history_entry"
        ) as mock_get_history, patch.object(
            comfyui_requests, "_check_for_output_success"
        ) as mock_check_success, patch.object(
            comfyui_requests, "_get_output_paths"
        ) as mock_get_paths:

            # Setup mocks
            mock_response = Mock()
            mock_response.json.return_value = {"prompt_id": "prompt_123"}
            mock_submit.return_value = mock_response
            mock_wait.return_value = 25
            mock_get_history.return_value = {
                "status": {"status_str": "success", "completed": True}
            }
            mock_get_paths.return_value = ["/output/result.png"]

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow)

            # Assert
            assert result == ["/output/result.png"]
            mock_submit.assert_called_once_with(mock_workflow)
            mock_wait.assert_called_once_with("prompt_123")
            mock_get_history.assert_called_once()
            mock_check_success.assert_called_once()
            mock_get_paths.assert_called_once()

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_process_single_workflow_runtime_error_retry(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test workflow processing with RuntimeError and successful retry - tests retry mechanism."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"

        with patch.object(
            comfyui_requests, "_submit_single_prompt"
        ) as mock_submit, patch.object(
            comfyui_requests, "_wait_for_completion"
        ) as mock_wait, patch.object(
            comfyui_requests, "get_last_history_entry"
        ) as mock_get_history, patch.object(
            comfyui_requests, "_check_for_output_success"
        ) as mock_check_success, patch.object(
            comfyui_requests, "_get_output_paths"
        ) as mock_get_paths:

            # Setup mocks - first attempt fails, second succeeds
            mock_response = Mock()
            mock_response.json.return_value = {"prompt_id": "prompt_123"}
            mock_submit.return_value = mock_response
            mock_wait.return_value = 30
            mock_get_history.return_value = {
                "status": {"status_str": "success", "completed": True}
            }
            mock_check_success.side_effect = [
                RuntimeError("First attempt failed"),
                None,
            ]  # Fail then succeed
            mock_get_paths.return_value = ["/output/result.png"]

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow)

            # Assert
            assert result == ["/output/result.png"]
            assert mock_submit.call_count == 2  # Should retry once
            assert mock_check_success.call_count == 2
            assert (
                mock_sleep.call_count == 4
            )  # Each attempt: sleep in _send_clean_memory_request (3s) + sleep delay_seconds

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_process_single_workflow_request_exception_retry(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test workflow processing with RequestException and successful retry - tests different exception handling."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"

        with patch.object(
            comfyui_requests, "_submit_single_prompt"
        ) as mock_submit, patch.object(
            comfyui_requests, "_wait_for_completion"
        ) as mock_wait, patch.object(
            comfyui_requests, "get_last_history_entry"
        ) as mock_get_history, patch.object(
            comfyui_requests, "_check_for_output_success"
        ) as mock_check_success, patch.object(
            comfyui_requests, "_get_output_paths"
        ) as mock_get_paths:

            # Setup mocks - first submit fails with RequestException, second succeeds
            mock_response = Mock()
            mock_response.json.return_value = {"prompt_id": "prompt_456"}
            mock_submit.side_effect = [
                RequestException("Connection failed"),
                mock_response,
            ]
            mock_wait.return_value = 20
            mock_get_history.return_value = {
                "status": {"status_str": "success", "completed": True}
            }
            mock_get_paths.return_value = ["/output/retry_result.png"]

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow)

            # Assert
            assert result == ["/output/retry_result.png"]
            assert mock_submit.call_count == 2
            assert (
                mock_sleep.call_count == 4
            )  # Each attempt: sleep in _send_clean_memory_request (3s) + sleep delay_seconds

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_process_single_workflow_max_retries_exceeded(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test workflow processing when max retries are exceeded - tests failure propagation."""
        # Arrange
        comfyui_requests.max_retries_per_request = 2  # Set low retry count for testing
        mock_workflow.get_workflow_summary.return_value = "failing_workflow"

        with patch.object(comfyui_requests, "_submit_single_prompt") as mock_submit:
            # Always fail with RuntimeError
            mock_submit.side_effect = RuntimeError("Persistent failure")

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow)

            # Assert
            assert result == []  # Should return empty list after all retries exhausted
            assert (
                mock_submit.call_count == 2
            )  # Should try exactly max_retries_per_request times
            assert (
                mock_sleep.call_count == 3
            )  # Attempt 1: _send_clean_memory_request (3s) + delay_seconds; Attempt 2: _send_clean_memory_request (3s) only

    @patch("ai_video_creator.comfyui.comfyui_requests.time.sleep")
    def test_process_single_workflow_no_history_entry(
        self, mock_sleep, comfyui_requests, mock_workflow
    ):
        """Test workflow processing when no history entry is found - tests edge case handling and retry logic."""
        # Arrange
        mock_workflow.get_workflow_summary.return_value = "test_workflow"

        with patch.object(
            comfyui_requests, "_submit_single_prompt"
        ) as mock_submit, patch.object(
            comfyui_requests, "_wait_for_completion"
        ) as mock_wait, patch.object(
            comfyui_requests, "get_last_history_entry"
        ) as mock_get_history:

            mock_response = Mock()
            mock_response.json.return_value = {"prompt_id": "prompt_123"}
            mock_submit.return_value = mock_response
            mock_wait.return_value = 15
            mock_get_history.return_value = (
                {}
            )  # Empty history - this triggers the retry logic

            # Act
            result = comfyui_requests._process_single_workflow(mock_workflow)

            # Assert
            assert result == []
            # Should retry up to max_retries_per_request times (default is 5 from fixture, but we set it to 3)
            assert mock_submit.call_count == comfyui_requests.max_retries_per_request
            assert mock_wait.call_count == comfyui_requests.max_retries_per_request
            assert (
                mock_get_history.call_count == comfyui_requests.max_retries_per_request
            )
            # Each attempt: _send_clean_memory_request sleeps, plus delay_seconds for all but last attempt
            # With max_retries=3: 3 sleeps from _send_clean_memory_request + 2 sleeps from delay_seconds = 5 total
            assert mock_sleep.call_count == comfyui_requests.max_retries_per_request + (
                comfyui_requests.max_retries_per_request - 1
            )
