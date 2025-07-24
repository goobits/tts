"""Tests for input parsing and text processing functionality.

These tests cover the input parsing logic that handles both JSON and
plain text inputs, extracting parameters and text content appropriately.
Tests pure functions without requiring external dependencies.
"""

from tts.cli import parse_input


class TestParseInput:
    """Test input parsing for JSON and plain text formats."""

    def test_valid_json_with_text(self):
        """Test parsing valid JSON input with text field."""
        json_input = '{"text": "Hello world", "voice": "nova", "rate": "fast"}'
        text, params = parse_input(json_input)

        assert text == "Hello world"
        assert params == {"voice": "nova", "rate": "fast"}

    def test_valid_json_minimal(self):
        """Test parsing minimal valid JSON with only text."""
        json_input = '{"text": "Simple message"}'
        text, params = parse_input(json_input)

        assert text == "Simple message"
        assert params == {}

    def test_valid_json_no_text_field(self):
        """Test parsing valid JSON without text field (should fall back to plain text)."""
        json_input = '{"voice": "nova", "rate": "fast"}'
        text, params = parse_input(json_input)

        # Should return the original JSON string as text
        assert text == json_input
        assert params == {}

    def test_valid_json_empty_text(self):
        """Test parsing valid JSON with empty text field."""
        json_input = '{"text": "", "voice": "nova"}'
        text, params = parse_input(json_input)

        assert text == ""
        assert params == {"voice": "nova"}

    def test_valid_json_complex_parameters(self):
        """Test parsing JSON with various parameter types."""
        json_input = '''
        {
            "text": "Complex message",
            "voice": "en-US-JennyNeural",
            "rate": 1.2,
            "pitch": "+2st",
            "volume": 0.8,
            "save": true,
            "format": "mp3",
            "metadata": {"author": "test", "tags": ["speech", "demo"]}
        }
        '''
        text, params = parse_input(json_input)

        assert text == "Complex message"
        assert params["voice"] == "en-US-JennyNeural"
        assert params["rate"] == 1.2
        assert params["pitch"] == "+2st"
        assert params["volume"] == 0.8
        assert params["save"] is True
        assert params["format"] == "mp3"
        assert params["metadata"]["author"] == "test"
        assert params["metadata"]["tags"] == ["speech", "demo"]

    def test_valid_json_with_whitespace(self):
        """Test parsing JSON with extra whitespace."""
        json_inputs = [
            '  {"text": "Hello", "voice": "nova"}  ',
            '\n{"text": "Hello", "voice": "nova"}\n',
            '\t{"text": "Hello", "voice": "nova"}\t',
            '   \n\t  {"text": "Hello", "voice": "nova"}  \t\n   ',
        ]

        for json_input in json_inputs:
            text, params = parse_input(json_input)
            assert text == "Hello"
            assert params == {"voice": "nova"}

    def test_invalid_json_malformed(self):
        """Test parsing malformed JSON (should fall back to plain text)."""
        invalid_json_inputs = [
            '{"text": "Hello", "voice": nova}',  # Missing quotes around nova
            '{"text": "Hello" "voice": "nova"}',  # Missing comma
            '{"text": "Hello", voice": "nova"}',  # Missing opening quote
            '{text": "Hello", "voice": "nova"}',  # Missing opening quote
            '{"text": "Hello", "voice": "nova"',  # Missing closing brace
            '{"text": "Hello", "voice": "nova"}}',  # Extra closing brace
            '{invalid json structure}',
            '{"text": "Hello", }',  # Trailing comma
        ]

        for invalid_input in invalid_json_inputs:
            text, params = parse_input(invalid_input)
            # Should return the original string as plain text
            assert text == invalid_input
            assert params == {}

    def test_invalid_json_empty_braces(self):
        """Test parsing empty or minimal JSON structures."""
        edge_case_inputs = [
            '{}',  # Empty JSON object
            '{   }',  # Empty with whitespace
            '{ }',  # Empty with space
        ]

        for json_input in edge_case_inputs:
            text, params = parse_input(json_input)
            # Should return original string since no 'text' field
            assert text == json_input
            assert params == {}

    def test_plain_text_simple(self):
        """Test parsing simple plain text input."""
        plain_texts = [
            "Hello world",
            "Simple message",
            "How are you today?",
            "Text with numbers 123",
            "Text with symbols !@#$%",
        ]

        for plain_text in plain_texts:
            text, params = parse_input(plain_text)
            assert text == plain_text
            assert params == {}

    def test_plain_text_with_braces_not_json(self):
        """Test plain text that contains braces but isn't JSON."""
        non_json_with_braces = [
            "This {is not} JSON",
            "Function call: func({param: value})",
            "CSS: body { margin: 0; }",
            "Template: Hello {name}!",
            "Math: {x | x > 0}",
            "{this starts with brace but isn't JSON",
            "} this ends with brace {",
        ]

        for text_input in non_json_with_braces:
            text, params = parse_input(text_input)
            assert text == text_input
            assert params == {}


    def test_json_with_special_characters(self):
        """Test parsing JSON with special characters in text."""
        special_text_cases = [
            ('{"text": "Hello\\"world\\""}', 'Hello"world"'),  # Escaped quotes
            ('{"text": "Line 1\\nLine 2"}', 'Line 1\nLine 2'),  # Newlines
            ('{"text": "Tab\\there"}', 'Tab\there'),  # Tabs
            ('{"text": "Unicode: café 🎉"}', 'Unicode: café 🎉'),  # Unicode
            ('{"text": "Backslash: \\\\"}', 'Backslash: \\'),  # Escaped backslash
            ('{"text": "Forward/slash"}', 'Forward/slash'),  # Forward slash
        ]

        for json_input, expected_text in special_text_cases:
            text, params = parse_input(json_input)
            assert text == expected_text

    def test_json_text_field_various_types(self):
        """Test JSON where text field has various data types."""
        # Only string text should be extracted, others should fall back to plain text
        type_test_cases = [
            ('{"text": 123}', '{"text": 123}'),  # Number - should fall back
            ('{"text": true}', '{"text": true}'),  # Boolean - should fall back
            ('{"text": null}', '{"text": null}'),  # Null - should fall back
            ('{"text": []}', '{"text": []}'),  # Array - should fall back
            ('{"text": {}}', '{"text": {}}'),  # Object - should fall back
            ('{"text": "valid string"}', 'valid string'),  # String - should work
        ]

        for json_input, expected_text in type_test_cases:
            text, params = parse_input(json_input)
            assert text == expected_text

    def test_json_parameter_extraction(self):
        """Test that parameters are correctly extracted after text removal."""
        json_input = '''
        {
            "text": "The message",
            "voice": "nova",
            "rate": "slow",
            "pitch": "+1st",
            "volume": 0.9,
            "save": false,
            "format": "wav"
        }
        '''

        text, params = parse_input(json_input)

        assert text == "The message"
        # Text should be removed from params
        assert "text" not in params
        # All other parameters should be preserved
        expected_params = {
            "voice": "nova",
            "rate": "slow",
            "pitch": "+1st",
            "volume": 0.9,
            "save": False,
            "format": "wav"
        }
        assert params == expected_params

    def test_json_nested_structures(self):
        """Test parsing JSON with nested objects and arrays."""
        complex_json = '''
        {
            "text": "Complex structure",
            "voice_config": {
                "provider": "openai",
                "voice": "nova",
                "settings": {
                    "rate": 1.0,
                    "pitch": 0.0
                }
            },
            "outputs": ["mp3", "wav"],
            "metadata": {
                "tags": ["test", "demo"],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        '''

        text, params = parse_input(complex_json)

        assert text == "Complex structure"
        assert "text" not in params
        assert params["voice_config"]["provider"] == "openai"
        assert params["voice_config"]["settings"]["rate"] == 1.0
        assert params["outputs"] == ["mp3", "wav"]
        assert params["metadata"]["tags"] == ["test", "demo"]


    def test_large_inputs(self):
        """Test parsing with large inputs."""
        # Large plain text
        large_text = "A" * 10000
        text, params = parse_input(large_text)
        assert text == large_text
        assert params == {}

        # Large JSON text field
        large_json_text = "B" * 5000
        json_input = f'{{"text": "{large_json_text}", "voice": "nova"}}'
        text, params = parse_input(json_input)
        assert text == large_json_text
        assert params == {"voice": "nova"}

    def test_edge_case_json_structures(self):
        """Test edge cases in JSON structure detection."""
        edge_cases = [
            # JSON-like but not starting with {
            ('["text", "hello"]', '["text", "hello"]'),  # Array
            ('null', 'null'),  # Null value
            ('123', '123'),  # Number
            ('"string"', '"string"'),  # Quoted string

            # Starting with { but complex cases
            ('{{nested}}', '{{nested}}'),  # Invalid nested braces
            ('{', '{'),  # Just opening brace
            ('{ "incomplete"', '{ "incomplete"'),  # Incomplete JSON
        ]

        for input_text, expected_output in edge_cases:
            text, params = parse_input(input_text)
            assert text == expected_output
            assert params == {}

