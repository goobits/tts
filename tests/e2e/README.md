# End-to-End Test Suite for TTS CLI

This directory contains comprehensive end-to-end tests for the TTS CLI system, including workflow tests, performance benchmarks, and CI/CD integration configurations.

## Test Structure

### Core E2E Test Files

1. **`test_complete_workflows.py`** - Complete user workflows from CLI input to audio output
   - Basic text-to-speech synthesis workflows
   - Document processing workflows (HTML, Markdown, JSON)
   - Complex multi-step scenarios
   - Error recovery workflows

2. **`test_pipeline_integration.py`** - Multi-provider pipeline tests
   - Cross-provider performance comparison
   - Provider fallback mechanisms
   - Configuration-based provider selection
   - Concurrent multi-provider synthesis

3. **`test_real_user_scenarios.py`** - Realistic usage patterns
   - Content creation scenarios (podcasts, education, marketing)
   - Document processing scenarios (research papers, emails, web content)
   - Accessibility scenarios (screen reader content, language learning)
   - Complex real-world workflows (audiobooks, emergency notifications)

4. **`test_performance_benchmarks.py`** - Performance benchmarking and baselines
   - Synthesis performance across text lengths
   - Provider performance comparison
   - Format performance comparison
   - Stress and scalability benchmarks
   - Performance regression detection

5. **`test_stress_regression.py`** - Stress testing and regression detection
   - Memory leak detection
   - High concurrency stress tests
   - Resource exhaustion handling
   - Comprehensive regression detection

## Test Categories and Markers

### Pytest Markers

- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.workflow` - Workflow-specific tests
- `@pytest.mark.pipeline` - Pipeline integration tests
- `@pytest.mark.realuser` - Real user scenario tests
- `@pytest.mark.benchmark` - Performance benchmark tests
- `@pytest.mark.performance` - Performance-related tests
- `@pytest.mark.stress` - Stress testing
- `@pytest.mark.regression` - Regression detection tests
- `@pytest.mark.slow` - Tests that take longer to run

### Test Execution

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test categories
pytest tests/e2e/ -m "e2e and workflow" -v
pytest tests/e2e/ -m "benchmark" -v
pytest tests/e2e/ -m "stress" -v

# Run with specific environment variables
TEST_REAL_PROVIDERS=1 pytest tests/e2e/test_pipeline_integration.py -v
TEST_PERFORMANCE_WORKFLOWS=1 pytest tests/e2e/test_complete_workflows.py -v
TEST_COMPLEX_SCENARIOS=1 pytest tests/e2e/test_real_user_scenarios.py -v
TEST_MEMORY_STRESS=1 pytest tests/e2e/test_stress_regression.py -v
TEST_RESOURCE_EXHAUSTION=1 pytest tests/e2e/test_stress_regression.py -v

# Run performance benchmarks only
pytest tests/e2e/test_performance_benchmarks.py -v

# Run stress tests (requires environment variable)
TEST_MEMORY_STRESS=1 pytest tests/e2e/test_stress_regression.py::TestMemoryLeakDetection -v
```

## Performance Baselines and Metrics

### Performance Thresholds

The test suite establishes the following performance thresholds:

- **Maximum synthesis time**: 60 seconds
- **Maximum real-time factor**: 10x (synthesis should be < 10x real-time)
- **Maximum memory usage**: 500 MB
- **Maximum CPU usage**: 80%
- **Minimum words per minute**: 100 WPM
- **Maximum words per minute**: 300 WPM
- **Synthesis success rate**: 80% minimum

### Baseline Files

- `performance_baselines.json` - Established performance baselines
- `latest_benchmark_results.json` - Most recent benchmark results

### Performance Regression Detection

The test suite automatically:
- Compares current performance against baselines
- Detects regressions (>20% performance degradation)
- Updates baselines when tests improve
- Flags critical performance issues

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  e2e-basic:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg sox
    
    - name: Install TTS CLI
      run: |
        ./setup.sh install --dev
    
    - name: Run basic E2E tests
      run: |
        pytest tests/e2e/test_complete_workflows.py::TestBasicSynthesisWorkflows -v
        pytest tests/e2e/test_pipeline_integration.py::TestMultiProviderComparison -v
      env:
        PYTHONDONTWRITEBYTECODE: 1
    
    - name: Upload test artifacts
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: e2e-test-artifacts
        path: |
          tests/e2e/performance_baselines.json
          tests/e2e/latest_benchmark_results.json

  e2e-performance:
    runs-on: ubuntu-latest
    needs: e2e-basic
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.10
      uses: actions/setup-python@v3
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg sox
        ./setup.sh install --dev
    
    - name: Run performance benchmarks
      run: |
        pytest tests/e2e/test_performance_benchmarks.py -v
      env:
        PYTHONDONTWRITEBYTECODE: 1
    
    - name: Upload performance results
      uses: actions/upload-artifact@v3
      with:
        name: performance-benchmarks
        path: |
          tests/e2e/performance_baselines.json
          tests/e2e/latest_benchmark_results.json

  e2e-stress:
    runs-on: ubuntu-latest
    needs: e2e-basic
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[stress-test]')
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.10
      uses: actions/setup-python@v3
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg sox
        ./setup.sh install --dev
    
    - name: Run stress tests
      run: |
        pytest tests/e2e/test_stress_regression.py -v
      env:
        TEST_MEMORY_STRESS: 1
        TEST_RESOURCE_EXHAUSTION: 1
        PYTHONDONTWRITEBYTECODE: 1
      timeout-minutes: 30
    
    - name: Upload stress test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: stress-test-results
        path: |
          tests/e2e/regression_test_results.json

  e2e-real-scenarios:
    runs-on: ubuntu-latest
    needs: e2e-basic
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.10
      uses: actions/setup-python@v3
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg sox
        ./setup.sh install --dev
    
    - name: Run real user scenarios
      run: |
        pytest tests/e2e/test_real_user_scenarios.py -v
      env:
        TEST_COMPLEX_SCENARIOS: 1
        PYTHONDONTWRITEBYTECODE: 1
```

### Local Development Integration

```bash
# Pre-commit hook for performance regression detection
#!/bin/bash
# .git/hooks/pre-commit

echo "Running E2E performance regression check..."
python -m pytest tests/e2e/test_performance_benchmarks.py::TestPerformanceRegression::test_baseline_performance_comparison -v

if [ $? -ne 0 ]; then
    echo "Performance regression detected! Commit blocked."
    exit 1
fi

echo "Performance regression check passed."
```

### Performance Monitoring

```bash
# Performance monitoring script
#!/bin/bash
# scripts/monitor_performance.sh

# Run performance benchmarks
pytest tests/e2e/test_performance_benchmarks.py -v --tb=short

# Generate performance report
python scripts/generate_performance_report.py

# Upload to monitoring service (example)
curl -X POST "https://monitoring.example.com/api/performance" \
  -H "Content-Type: application/json" \
  -d @tests/e2e/latest_benchmark_results.json
```

## Environment Variables

### Test Configuration

- `TEST_REAL_PROVIDERS=1` - Enable real provider testing (requires API keys)
- `TEST_PERFORMANCE_WORKFLOWS=1` - Enable performance workflow testing
- `TEST_COMPLEX_SCENARIOS=1` - Enable complex scenario testing
- `TEST_MEMORY_STRESS=1` - Enable memory stress testing
- `TEST_RESOURCE_EXHAUSTION=1` - Enable resource exhaustion testing
- `TEST_PROVIDER_EXHAUSTIVE=1` - Enable exhaustive provider testing

### Provider Configuration

```bash
# For real provider testing
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export ELEVENLABS_API_KEY="your-elevenlabs-key"
```

## Test Data and Fixtures

### Test Fixtures Directory

The `tests/fixtures/` directory contains:
- Sample documents for testing (HTML, Markdown, JSON)
- Expected audio validation data
- Performance baseline data

### Audio Validation

All E2E tests use the comprehensive audio validation framework:
- File format validation
- Duration and quality checks
- Silence detection
- Metadata extraction
- Performance metrics

## Troubleshooting

### Common Issues

1. **Provider Unavailable**: Tests automatically skip when providers are not configured
2. **Memory Issues**: Stress tests include memory cleanup and garbage collection
3. **Timeout Issues**: Tests have appropriate timeouts for different operations
4. **File System Issues**: Tests clean up temporary files automatically

### Debug Mode

```bash
# Run with verbose output and debug information
pytest tests/e2e/ -v -s --tb=long

# Run specific test with debug output
pytest tests/e2e/test_complete_workflows.py::TestBasicSynthesisWorkflows::test_complete_text_to_audio_workflow -v -s
```

### Performance Debugging

```bash
# Profile memory usage
python -m pytest tests/e2e/test_stress_regression.py::TestMemoryLeakDetection -v --profile

# Monitor system resources during tests
htop &
pytest tests/e2e/test_performance_benchmarks.py -v
```

## Contributing

When adding new E2E tests:

1. Use appropriate pytest markers
2. Include comprehensive error handling
3. Implement proper cleanup
4. Add performance assertions where relevant
5. Document test scenarios and expected outcomes
6. Consider CI/CD impact and execution time

## Reporting

The E2E test suite generates several types of reports:

- **Performance Benchmarks**: JSON reports with detailed metrics
- **Regression Analysis**: Comparison reports against baselines
- **Stress Test Results**: Memory and resource usage reports
- **User Scenario Results**: User experience metrics and satisfaction scores

These reports can be integrated with monitoring systems and used for continuous performance tracking.