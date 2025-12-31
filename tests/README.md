# Matilda Voice Test Suite

This document describes the test organization structure for Matilda Voice.

## Directory Structure

```
tests/
├── README.md                     # This documentation
├── conftest.py                   # Main test configuration and fixtures
├── __init__.py                   # Package init
│
├── utils/                        # Shared test utilities
│   ├── __init__.py
│   └── test_helpers.py           # Common fixtures, helpers, and utilities
│
├── fixtures/                     # Test data files
│   ├── data_export.json
│   ├── marketing_page.html
│   └── ...
│
├── mocking/                      # Mock infrastructure
│   ├── audio_mocks.py
│   ├── network_mocks.py
│   └── provider_mocks.py
│
├── providers/                    # Provider-specific tests
│   └── test_edge_tts.py
│
├── unit/                         # Pure unit tests
│   ├── test_config.py            # Configuration management tests
│   ├── test_exceptions.py        # Exception handling tests
│   ├── test_audio_utils.py       # Audio utility tests
│   ├── test_cli_formats.py       # CLI format tests
│   ├── test_utils_validation.py  # Validation utility tests
│   └── test_voice_analysis.py    # Voice analysis tests
│
├── integration/                  # Integration tests
│   ├── test_cli_integration.py   # Core CLI functionality
│   ├── test_cli_config.py        # CLI configuration commands
│   ├── test_audio_validation.py  # Audio validation tests
│   ├── test_real_audio_synthesis.py  # Real audio synthesis tests
│   └── providers/                # Provider integration tests
│       ├── test_openai_integration.py
│       ├── test_google_integration.py
│       ├── test_chatterbox_integration.py
│       └── test_elevenlabs_integration.py
│
├── e2e/                          # End-to-end tests
│   ├── test_cli_smoke.py         # Comprehensive smoke tests
│   ├── test_cli_real_integration.py  # Real integration tests
│   ├── test_pipeline_integration.py  # Pipeline workflow tests
│   └── test_complete_workflows.py    # Complete workflow tests
│
└── Root-level tests              # Tests pending migration
    ├── test_cli.py               # Basic CLI tests
    ├── test_cli_document.py      # Document processing CLI tests
    ├── test_document_processing.py  # Document processing tests
    └── test_tts_engine.py        # TTS engine tests
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions, classes, and modules in isolation
- **Dependencies**: Minimal external dependencies, mostly using stubs/mocks
- **Speed**: Fast execution (< 1 second per test)
- **Examples**: Configuration parsing, exception handling, utility functions

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interaction between multiple components
- **Dependencies**: Real provider logic with mocked external calls
- **Speed**: Medium execution (1-5 seconds per test)
- **Examples**: CLI commands, provider integration, voice management

### End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows from user perspective
- **Dependencies**: Comprehensive mocking or real external services
- **Speed**: Slower execution (5+ seconds per test)
- **Examples**: Full CLI smoke tests, real provider integration

### Provider Tests (`tests/providers/`)
- **Purpose**: Test provider-specific implementations
- **Dependencies**: Provider SDKs with mocked API calls
- **Speed**: Medium execution
- **Examples**: Edge TTS voice listing, synthesis calls

## Shared Utilities (`tests/utils/`)

The `test_helpers.py` module provides reusable utilities:

### Key Utilities

1. **CLITestHelper**: Simplified CLI command invocation and assertion
   ```python
   cli_helper = CLITestHelper()
   result, output_path = cli_helper.invoke_save("text", provider="@edge")
   cli_helper.assert_success(result)
   ```

2. **Provider Test Helpers**: Mock provider creation and validation
   ```python
   mock_provider = create_mock_provider("test_provider", voices=["voice1", "voice2"])
   assert_provider_called_with(mock_provider, "expected text", voice="voice1")
   ```

3. **Audio File Utilities**: Audio file creation and validation
   ```python
   audio_file = create_mock_audio_file(path, format="mp3", size_bytes=1024)
   assert validate_audio_file(audio_file, expected_format="mp3")
   ```

4. **Configuration Helpers**: Test configuration creation
   ```python
   config_file = create_test_config(config_dir, default_provider="edge_tts")
   ```

## Running Tests

### All Tests
```bash
# Using the test script (recommended)
./scripts/test.sh

# Direct pytest with coverage
python -m pytest tests/ --cov=matilda_voice --cov-report=html
```

### By Category
```bash
# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# End-to-end tests only (slower)
python -m pytest tests/e2e/ -v

# Provider tests
python -m pytest tests/providers/ -v
```

### Specific Test Files
```bash
# CLI integration tests
python -m pytest tests/integration/test_cli_integration.py -v

# Smoke tests
python -m pytest tests/e2e/test_cli_smoke.py -v

# Single test function
python -m pytest tests/unit/test_config.py::test_function_name -v
```

## Test Configuration

### conftest.py Features
- Automatic audio environment mocking
- Provider mock fixtures
- Temporary directory management
- CLI runner setup

### Environment Variables
- `SKIP_AUDIO_TESTS=1` - Skip tests requiring audio hardware
- `SKIP_NETWORK_TESTS=1` - Skip tests requiring network access

## Best Practices

1. **Use Shared Utilities**: Prefer `CLITestHelper` over manual CLI invocation
2. **Mock External Services**: All provider API calls should be mocked in unit/integration tests
3. **Clear Test Categories**: Place tests in appropriate directories based on their scope
4. **Descriptive Names**: Use clear, descriptive test function names
5. **Fixture Reuse**: Use conftest.py fixtures for common setup

## Future Improvements

1. **Complete Migration**: Move remaining root-level tests to appropriate directories
2. **Parallel Testing**: Optimize test suite for parallel execution with pytest-xdist
3. **CI Integration**: Optimize test organization for CI/CD pipelines
