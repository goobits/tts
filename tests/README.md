# TTS CLI Test Suite Organization

This document describes the improved test organization structure implemented to reduce duplication and improve maintainability.

## Directory Structure

```
tests/
├── README.md                     # This documentation
├── conftest.py                   # Main test configuration and fixtures
├── cli-test-checklist.md         # Legacy test checklist
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
│   └── test_audio_utils.py       # Audio utility tests
│
├── integration/                  # Integration tests
│   ├── test_cli.py               # Core CLI functionality
│   ├── test_cli_config.py        # CLI configuration commands
│   ├── test_cli_save_consolidated.py        # Consolidated save tests
│   └── test_provider_shortcuts_consolidated.py  # Consolidated shortcut tests
│
├── e2e/                          # End-to-end tests
│   ├── test_cli_smoke.py         # Comprehensive smoke tests
│   └── test_cli_real_integration.py  # Real integration tests
│
└── Remaining files...            # Files not yet reorganized
    ├── test_cli_document.py
    ├── test_cli_formats.py
    ├── test_document_processing.py
    └── test_voice_analysis.py
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

## Shared Utilities (`tests/utils/`)

The `test_helpers.py` module provides reusable utilities to eliminate duplication:

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

5. **Parameterized Test Support**: Provider shortcuts testing
   ```python
   @parametrize_provider_shortcuts()
   def test_provider_shortcuts(shortcut, provider_name):
       # Test all provider shortcuts automatically
   ```

### Factory Fixtures

- `cli_helper`: CLITestHelper instance
- `mock_provider_factory`: Factory for creating mock providers
- `temp_audio_factory`: Factory for creating temporary audio files
- `config_factory`: Factory for creating test configurations

## Eliminated Duplicates

### Before Consolidation
- **Save functionality tests**: 15+ duplicate tests across 3 files (~150 lines)
- **Provider shortcut tests**: 12+ duplicate tests across 3 files (~120 lines)
- **CLI environment setup**: Repeated setup in every test file
- **Audio file validation**: Copy-pasted validation logic

### After Consolidation
- **Save functionality**: Consolidated into `test_cli_save_consolidated.py` (~80 lines)
- **Provider shortcuts**: Consolidated into `test_provider_shortcuts_consolidated.py` (~90 lines)
- **CLI environment**: Reusable `CLITestHelper` class
- **Audio validation**: Shared `validate_audio_file()` function

**Total reduction**: ~200 lines of duplicate code eliminated

## Migration Status

### Moved Files
✅ `test_config.py` → `tests/unit/`
✅ `test_exceptions.py` → `tests/unit/`
✅ `test_audio_utils.py` → `tests/unit/`
✅ `test_cli.py` → `tests/integration/`
✅ `test_cli_config.py` → `tests/integration/`
✅ `test_cli_smoke.py` → `tests/e2e/`
✅ `test_cli_real_integration.py` → `tests/e2e/`

### New Consolidated Files
✅ `tests/integration/test_cli_save_consolidated.py`
✅ `tests/integration/test_provider_shortcuts_consolidated.py`

### Pending Migration
- `test_cli_document.py` - Document processing CLI tests
- `test_cli_formats.py` - Audio format validation tests
- `test_document_processing.py` - Document processing unit tests
- `test_voice_analysis.py` - Voice analysis tests

## Running Tests

### By Category
```bash
# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests only (medium)
python -m pytest tests/integration/ -v

# End-to-end tests only (slower)
python -m pytest tests/e2e/ -v

# All tests with coverage
./test.sh
```

### Specific Test Suites
```bash
# Consolidated save tests
python -m pytest tests/integration/test_cli_save_consolidated.py -v

# Provider shortcuts tests
python -m pytest tests/integration/test_provider_shortcuts_consolidated.py -v

# Smoke tests
python -m pytest tests/e2e/test_cli_smoke.py -v
```

### Using Test Utilities
```bash
# Tests that use shared utilities
python -m pytest -k "consolidated" -v

# All tests (including old structure)
python -m pytest tests/ -v
```

## Benefits of New Structure

1. **Reduced Duplication**: ~200 lines of duplicate test code eliminated
2. **Better Organization**: Clear separation of unit/integration/e2e tests
3. **Improved Maintainability**: Shared utilities reduce maintenance burden
4. **Faster Development**: Reusable helpers speed up new test creation
5. **Consistent Testing**: Standardized patterns across all tests
6. **Better Coverage**: Comprehensive testing without redundancy

## Best Practices

1. **Use Shared Utilities**: Prefer `CLITestHelper` over manual CLI invocation
2. **Parameterize Tests**: Use `@parametrize_provider_shortcuts()` for provider testing
3. **Factory Fixtures**: Use factories for creating test data
4. **Clear Test Categories**: Place tests in appropriate directories
5. **Descriptive Names**: Use clear, descriptive test function names
6. **Minimal Mocking**: Use the tiered fixture architecture (minimal → unit → integration → full)

## Future Improvements

1. **Complete Migration**: Move remaining test files to appropriate directories
2. **More Utilities**: Add utilities for document processing, voice analysis
3. **Performance Testing**: Add performance benchmarks for critical paths
4. **Parallel Testing**: Optimize test suite for parallel execution
5. **CI Integration**: Optimize test organization for CI/CD pipelines