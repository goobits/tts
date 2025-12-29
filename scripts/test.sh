#!/bin/bash
# Enhanced test runner script with coverage reporting

echo "🧪 Running TTS CLI Tests"
echo "========================"

# Check if pytest is available
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found. Please install it:"
    echo "   pip install pytest pytest-cov"
    exit 1
fi

# Run tests with verbose output and coverage
echo "📊 Running tests with coverage..."
python3 -m pytest tests/ -v --tb=short --durations=10 

echo ""
echo "✅ Test run completed!"

# Optional: Run tests with coverage if pytest-cov is available
if python3 -c "import pytest_cov" 2>/dev/null; then
    echo ""
    echo "📈 Generating coverage report..."
    python3 -m pytest tests/ --cov=tts --cov-report=term-missing --cov-report=html:.temp/htmlcov
    echo ""
    echo "📋 Coverage report saved to .temp/htmlcov/index.html"
else
    echo ""
    echo "💡 For coverage reports, install: pip install pytest-cov"
fi