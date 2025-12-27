"""Tests for the SimpleTTSEngine class in speech_synthesis/tts_engine.py.

These tests cover the TTS engine functionality including:
- Engine detection and availability
- Speech synthesis with different emotions
- Timing and pause functionality
- Semantic element processing
- Error handling and fallback behavior
- Integration with system TTS commands
"""

import subprocess
from unittest.mock import MagicMock, call, patch

from matilda_voice.document_processing.base_parser import SemanticElement, SemanticType
from matilda_voice.speech_synthesis.tts_engine import SimpleTTSEngine


class TestSimpleTTSEngine:
    """Test the SimpleTTSEngine class functionality."""

    def test_init_detects_available_engines(self):
        """Test that initialization properly detects available TTS engines."""
        with patch.object(SimpleTTSEngine, '_detect_available_engines', return_value=['espeak', 'festival']) as mock_detect:
            engine = SimpleTTSEngine()

            assert engine.available_engines == ['espeak', 'festival']
            mock_detect.assert_called_once()

    def test_detect_espeak_available(self):
        """Test detection when espeak is available on the system."""
        with patch('subprocess.run') as mock_run:
            # Configure mock to succeed only for espeak
            def side_effect(cmd, **kwargs):
                if cmd[0] == 'espeak':
                    return MagicMock(returncode=0)
                else:
                    raise subprocess.CalledProcessError(1, cmd)

            mock_run.side_effect = side_effect

            engine = SimpleTTSEngine()
            assert 'espeak' in engine.available_engines
            assert 'festival' not in engine.available_engines
            assert 'say' not in engine.available_engines

    def test_detect_festival_available(self):
        """Test detection when festival is available on the system."""
        with patch('subprocess.run') as mock_run:
            # Configure mock to succeed only for festival
            def side_effect(cmd, **kwargs):
                if cmd[0] == 'festival':
                    return MagicMock(returncode=0)
                else:
                    raise subprocess.CalledProcessError(1, cmd)

            mock_run.side_effect = side_effect

            engine = SimpleTTSEngine()
            assert 'festival' in engine.available_engines
            assert 'espeak' not in engine.available_engines
            assert 'say' not in engine.available_engines

    def test_detect_say_available(self):
        """Test detection when macOS say command is available."""
        with patch('subprocess.run') as mock_run:
            # Configure mock to succeed only for say
            def side_effect(cmd, **kwargs):
                if cmd[0] == 'say':
                    return MagicMock(returncode=0)
                else:
                    raise subprocess.CalledProcessError(1, cmd)

            mock_run.side_effect = side_effect

            engine = SimpleTTSEngine()
            assert 'say' in engine.available_engines
            assert 'espeak' not in engine.available_engines
            assert 'festival' not in engine.available_engines

    def test_detect_no_engines_available(self):
        """Test detection when no TTS engines are available."""
        with patch('subprocess.run') as mock_run:
            # All commands fail
            mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')

            engine = SimpleTTSEngine()
            assert engine.available_engines == []

    def test_detect_handles_file_not_found(self):
        """Test that detection handles FileNotFoundError gracefully."""
        with patch('subprocess.run') as mock_run:
            # Simulate command not found
            mock_run.side_effect = FileNotFoundError("Command not found")

            engine = SimpleTTSEngine()
            assert engine.available_engines == []

    def test_detect_multiple_engines_available(self):
        """Test detection when multiple TTS engines are available."""
        with patch('subprocess.run') as mock_run:
            # All commands succeed
            mock_run.return_value = MagicMock(returncode=0)

            engine = SimpleTTSEngine()
            # Should detect all three engines
            assert set(engine.available_engines) == {'espeak', 'festival', 'say'}

            # Verify all detection commands were called
            expected_calls = [
                call(['espeak', '--version'], capture_output=True, check=True),
                call(['festival', '--version'], capture_output=True, check=True),
                call(['say', '-v', '?'], capture_output=True, check=True)
            ]
            mock_run.assert_has_calls(expected_calls, any_order=True)


class TestSpeakMethod:
    """Test the speak() method of SimpleTTSEngine."""

    def test_speak_with_no_engines_available(self, capsys):
        """Test speak behavior when no TTS engines are available."""
        engine = SimpleTTSEngine()
        engine.available_engines = []

        result = engine.speak("Hello world", "normal")

        assert result is False
        captured = capsys.readouterr()
        assert "[TTS] No TTS engine available. Would speak: Hello world" in captured.out

    def test_speak_with_espeak_normal_emotion(self):
        """Test speak with espeak using normal emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Test text", "normal")

            assert result is True
            mock_run.assert_called_once_with(
                ['espeak', '-p', '50', '-s', '160', 'Test text'],
                capture_output=True
            )

    def test_speak_with_espeak_excited_emotion(self):
        """Test speak with espeak using excited emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Exciting news!", "excited")

            assert result is True
            mock_run.assert_called_once_with(
                ['espeak', '-p', '60', '-s', '180', 'Exciting news!'],
                capture_output=True
            )

    def test_speak_with_espeak_soft_emotion(self):
        """Test speak with espeak using soft emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Gentle words", "soft")

            assert result is True
            mock_run.assert_called_once_with(
                ['espeak', '-p', '30', '-s', '120', 'Gentle words'],
                capture_output=True
            )

    def test_speak_with_espeak_monotone_emotion(self):
        """Test speak with espeak using monotone emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Code example", "monotone")

            assert result is True
            mock_run.assert_called_once_with(
                ['espeak', '-p', '40', '-s', '150', 'Code example'],
                capture_output=True
            )

    def test_speak_with_festival(self):
        """Test speak with festival (emotion parameter ignored)."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['festival']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Festival test", "excited")

            assert result is True
            mock_run.assert_called_once_with(
                ['festival', '--tts'],
                input='Festival test',
                text=True,
                capture_output=True
            )

    def test_speak_with_say_normal_emotion(self):
        """Test speak with macOS say command using normal emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Normal speech", "normal")

            assert result is True
            mock_run.assert_called_once_with(
                ['say', '-r', '160', 'Normal speech'],
                capture_output=True
            )

    def test_speak_with_say_excited_emotion(self):
        """Test speak with macOS say command using excited emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Exciting!", "excited")

            assert result is True
            mock_run.assert_called_once_with(
                ['say', '-v', 'Samantha', '-r', '200', 'Exciting!'],
                capture_output=True
            )

    def test_speak_with_say_soft_emotion(self):
        """Test speak with macOS say command using soft emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Whisper", "soft")

            assert result is True
            mock_run.assert_called_once_with(
                ['say', '-v', 'Whisper', '-r', '120', 'Whisper'],
                capture_output=True
            )

    def test_speak_with_say_monotone_emotion(self):
        """Test speak with macOS say command using monotone emotion."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Robotic", "monotone")

            assert result is True
            mock_run.assert_called_once_with(
                ['say', '-v', 'Ralph', '-r', '150', 'Robotic'],
                capture_output=True
            )

    def test_speak_handles_subprocess_failure(self):
        """Test speak handles subprocess returning non-zero exit code."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = engine.speak("Failed speech", "normal")

            assert result is False

    def test_speak_handles_exception(self, capsys):
        """Test speak handles exceptions during TTS execution."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Subprocess failed")

            result = engine.speak("Error speech", "normal")

            assert result is False
            captured = capsys.readouterr()
            assert "[TTS] Error with espeak: Subprocess failed" in captured.out
            assert "[TTS] Fallback - would speak: Error speech" in captured.out

    def test_speak_uses_first_available_engine(self):
        """Test that speak uses the first available engine in the list."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['festival', 'espeak', 'say']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Test priority", "normal")

            assert result is True
            # Should use festival (first in list)
            mock_run.assert_called_once_with(
                ['festival', '--tts'],
                input='Test priority',
                text=True,
                capture_output=True
            )


class TestSpeakWithEmotionMethod:
    """Test the speak_with_emotion() method with timing support."""

    def test_speak_with_emotion_no_engines(self, capsys):
        """Test speak_with_emotion when no engines are available."""
        engine = SimpleTTSEngine()
        engine.available_engines = []

        result = engine.speak_with_emotion("Test", "excited", 1.5)

        assert result is False
        captured = capsys.readouterr()
        assert "[TTS] No TTS engine available. Would speak with excited: Test" in captured.out
        assert "[TTS] Would pause for 1.5s" in captured.out

    def test_speak_with_emotion_and_timing(self):
        """Test speak_with_emotion with timing pause after speech."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak_with_emotion("Timed speech", "normal", 2.0)

            assert result is True
            mock_run.assert_called_once()
            mock_sleep.assert_called_once_with(2.0)

    def test_speak_with_emotion_no_timing(self):
        """Test speak_with_emotion without timing pause."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak_with_emotion("No pause", "normal", 0)

            assert result is True
            mock_run.assert_called_once()
            mock_sleep.assert_not_called()

    def test_speak_with_emotion_failed_speech_no_timing(self):
        """Test that timing pause is not applied when speech fails."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            mock_run.return_value = MagicMock(returncode=1)  # Failure

            result = engine.speak_with_emotion("Failed", "normal", 2.0)

            assert result is False
            mock_sleep.assert_not_called()  # No pause on failure

    def test_speak_with_emotion_exception_handling(self, capsys):
        """Test speak_with_emotion exception handling with timing info."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = RuntimeError("TTS crashed")

            result = engine.speak_with_emotion("Crash test", "soft", 3.0)

            assert result is False
            captured = capsys.readouterr()
            assert "[TTS] Error with say: TTS crashed" in captured.out
            assert "[TTS] Fallback - would speak with soft: Crash test" in captured.out
            assert "[TTS] Would pause for 3.0s" in captured.out

    def test_speak_with_emotion_different_engines(self):
        """Test speak_with_emotion delegates to correct engine methods."""
        test_cases = [
            ('espeak', 'excited', ['espeak', '-p', '60', '-s', '180', 'Test']),
            ('festival', 'soft', ['festival', '--tts']),
            ('say', 'monotone', ['say', '-v', 'Ralph', '-r', '150', 'Test'])
        ]

        for engine_name, emotion, expected_cmd in test_cases:
            engine = SimpleTTSEngine()
            engine.available_engines = [engine_name]

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = engine.speak_with_emotion("Test", emotion, 0)

                assert result is True
                if engine_name == 'festival':
                    mock_run.assert_called_once_with(
                        expected_cmd,
                        input='Test',
                        text=True,
                        capture_output=True
                    )
                else:
                    mock_run.assert_called_once_with(
                        expected_cmd,
                        capture_output=True
                    )


class TestSpeakElementsMethod:
    """Test the speak_elements() method for semantic element processing."""

    def test_speak_elements_empty_list(self):
        """Test speak_elements with empty element list."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        result = engine.speak_elements([])

        assert result is True  # Empty list is considered success

    def test_speak_elements_single_text_element(self):
        """Test speak_elements with a single text element."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        element = SemanticElement(
            type=SemanticType.TEXT,
            content="Plain text content"
        )

        with patch.object(engine, 'speak', return_value=True) as mock_speak:
            result = engine.speak_elements([element])

            assert result is True
            mock_speak.assert_called_once_with("Plain text content", "normal")

    def test_speak_elements_with_heading(self):
        """Test speak_elements with heading element (includes pauses)."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        element = SemanticElement(
            type=SemanticType.HEADING,
            content="Chapter Title",
            level=1
        )

        with patch.object(engine, 'speak', return_value=True) as mock_speak:
            result = engine.speak_elements([element])

            assert result is True
            # Should have 3 calls: pause before, heading, pause after
            assert mock_speak.call_count == 3
            calls = mock_speak.call_args_list
            assert calls[0] == call("", "normal")  # Pause before
            assert calls[1] == call("Chapter Title", "excited")  # Heading with excited emotion
            assert calls[2] == call("", "normal")  # Pause after

    def test_speak_elements_emotion_mapping(self):
        """Test that different element types get correct emotions."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        elements = [
            SemanticElement(type=SemanticType.HEADING, content="Title"),
            SemanticElement(type=SemanticType.BOLD, content="Important"),
            SemanticElement(type=SemanticType.ITALIC, content="Emphasis"),
            SemanticElement(type=SemanticType.CODE, content="var x = 1"),
            SemanticElement(type=SemanticType.CODE_BLOCK, content="function() {}"),
            SemanticElement(type=SemanticType.LIST_ITEM, content="Item 1"),
            SemanticElement(type=SemanticType.LINK, content="Click here"),
            SemanticElement(type=SemanticType.TEXT, content="Normal text"),
        ]

        expected_emotions = {
            SemanticType.HEADING: "excited",
            SemanticType.BOLD: "excited",
            SemanticType.ITALIC: "soft",
            SemanticType.CODE: "monotone",
            SemanticType.CODE_BLOCK: "monotone",
            SemanticType.LIST_ITEM: "normal",
            SemanticType.LINK: "normal",
            SemanticType.TEXT: "normal",
        }

        with patch.object(engine, 'speak', return_value=True) as mock_speak:
            result = engine.speak_elements(elements)

            assert result is True

            # Extract non-pause calls (content not empty)
            content_calls = [call for call in mock_speak.call_args_list if call[0][0]]

            for i, element in enumerate(elements):
                if element.type != SemanticType.HEADING:  # Headings have extra calls
                    call_args = content_calls[i][0]
                    assert call_args[0] == element.content
                    assert call_args[1] == expected_emotions[element.type]

    def test_speak_elements_mixed_success_failure(self):
        """Test speak_elements returns False if any element fails."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        elements = [
            SemanticElement(type=SemanticType.TEXT, content="Success 1"),
            SemanticElement(type=SemanticType.TEXT, content="Failure"),
            SemanticElement(type=SemanticType.TEXT, content="Success 2"),
        ]

        # Mock speak to fail on second element
        with patch.object(engine, 'speak') as mock_speak:
            mock_speak.side_effect = [True, False, True]

            result = engine.speak_elements(elements)

            assert result is False  # Overall failure
            assert mock_speak.call_count == 3  # All elements attempted

    def test_speak_elements_complex_document(self):
        """Test speak_elements with a complex document structure."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['festival']

        elements = [
            SemanticElement(type=SemanticType.HEADING, content="Introduction", level=1),
            SemanticElement(type=SemanticType.TEXT, content="This is the intro."),
            SemanticElement(type=SemanticType.HEADING, content="Code Example", level=2),
            SemanticElement(type=SemanticType.CODE_BLOCK, content="print('Hello')"),
            SemanticElement(type=SemanticType.TEXT, content="That was code."),
            SemanticElement(type=SemanticType.LIST_ITEM, content="First point"),
            SemanticElement(type=SemanticType.LIST_ITEM, content="Second point"),
        ]

        with patch.object(engine, 'speak', return_value=True) as mock_speak:
            result = engine.speak_elements(elements)

            assert result is True

            # Count pause calls vs content calls
            pause_calls = [call for call in mock_speak.call_args_list if call[0][0] == ""]
            content_calls = [call for call in mock_speak.call_args_list if call[0][0] != ""]

            # 2 headings = 4 pause calls (before and after each)
            assert len(pause_calls) == 4
            # 7 elements total
            assert len(content_calls) == 7

    def test_get_emotion_for_element_unknown_type(self):
        """Test _get_emotion_for_element returns 'normal' for unknown types."""
        engine = SimpleTTSEngine()

        # Create a new semantic type not in the emotion map
        unknown_element = SemanticElement(
            type=SemanticType.QUOTE,  # Not in emotion_map
            content="Quote text"
        )

        emotion = engine._get_emotion_for_element(unknown_element)
        assert emotion == "normal"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_speak_with_empty_text(self):
        """Test speak with empty text string."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("", "normal")

            assert result is True
            mock_run.assert_called_once_with(
                ['espeak', '-p', '50', '-s', '160', ''],
                capture_output=True
            )

    def test_speak_with_very_long_text(self):
        """Test speak with very long text content."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['festival']

        long_text = "A" * 10000  # 10k characters

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak(long_text, "normal")

            assert result is True
            mock_run.assert_called_once()
            # Verify the full text was passed
            call_args = mock_run.call_args
            assert call_args[1]['input'] == long_text

    def test_speak_with_special_characters(self):
        """Test speak with text containing special characters."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['say']

        special_text = "Hello! @#$%^&*() \"quoted\" 'text' with\nnewlines\tand\ttabs"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak(special_text, "normal")

            assert result is True
            mock_run.assert_called_once()
            # Text should be passed as-is
            assert special_text in mock_run.call_args[0][0]

    def test_speak_with_unicode_text(self):
        """Test speak with Unicode text content."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        unicode_text = "Hello 世界! Émojis: 😀 🎉 Symbols: ♥ ♦ ♣ ♠"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak(unicode_text, "normal")

            assert result is True
            mock_run.assert_called_once()
            assert unicode_text in mock_run.call_args[0][0]

    def test_subprocess_timeout_handling(self):
        """Test handling of subprocess timeout scenarios."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('espeak', 30)

            result = engine.speak("Timeout test", "normal")

            assert result is False

    def test_invalid_emotion_defaults_to_normal(self):
        """Test that invalid emotion strings don't cause errors."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak("Test", "invalid_emotion")

            assert result is True
            # Should use default/normal parameters
            mock_run.assert_called_once_with(
                ['espeak', '-p', '50', '-s', '160', 'Test'],
                capture_output=True
            )

    def test_speak_with_unknown_engine(self):
        """Test that speak returns False when unknown engine is in the list."""
        engine = SimpleTTSEngine()
        # Simulate unknown engine somehow getting into the list
        engine.available_engines = ['unknown_engine']

        result = engine.speak("Test", "normal")

        # Should return False since unknown engine isn't handled
        assert result is False


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_document_processing_workflow(self):
        """Test complete workflow from document elements to speech."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak', 'festival']  # Multiple engines available

        # Simulate a document with various elements
        document = [
            SemanticElement(type=SemanticType.HEADING, content="User Guide", level=1),
            SemanticElement(type=SemanticType.TEXT, content="Welcome to our application."),
            SemanticElement(type=SemanticType.HEADING, content="Getting Started", level=2),
            SemanticElement(type=SemanticType.TEXT, content="Follow these steps:"),
            SemanticElement(type=SemanticType.LIST_ITEM, content="Install the software"),
            SemanticElement(type=SemanticType.LIST_ITEM, content="Configure settings"),
            SemanticElement(type=SemanticType.CODE, content="config.set('key', 'value')"),
            SemanticElement(type=SemanticType.BOLD, content="Important:"),
            SemanticElement(type=SemanticType.ITALIC, content="Read the documentation"),
        ]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = engine.speak_elements(document)

            assert result is True
            # Should use espeak (first available)
            assert all('espeak' in str(call) for call in mock_run.call_args_list)

            # Verify different emotions were used
            call_strings = [str(call) for call in mock_run.call_args_list]
            assert any('-p\', \'60' in s for s in call_strings)  # Excited (headings/bold)
            assert any('-p\', \'30' in s for s in call_strings)  # Soft (italic)
            assert any('-p\', \'40' in s for s in call_strings)  # Monotone (code)
            assert any('-p\', \'50' in s for s in call_strings)  # Normal (text/list)

    def test_engine_fallback_on_primary_failure(self):
        """Test that engine falls back gracefully when primary engine fails."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']  # Set engines directly

        # First call succeeds
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert engine.speak("Success", "normal") is True

        # Second call fails
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Engine crashed")
            assert engine.speak("Failure", "normal") is False

    def test_timing_precision(self):
        """Test that timing delays are precise."""
        engine = SimpleTTSEngine()
        engine.available_engines = ['espeak']

        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            mock_run.return_value = MagicMock(returncode=0)

            # Test various timing values
            timings = [0.5, 1.0, 2.5, 0.1]

            for timing in timings:
                engine.speak_with_emotion("Test", "normal", timing)
                mock_sleep.assert_called_with(timing)
                mock_sleep.reset_mock()
