#!/bin/bash
# Performance monitoring script for Voice CLI
# This script runs performance benchmarks and generates monitoring reports

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_ROOT/tests/e2e"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MONITORING_LOG="$PROJECT_ROOT/logs/performance_monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$MONITORING_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$MONITORING_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$MONITORING_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$MONITORING_LOG"
}

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$MONITORING_LOG")"

# Function to check if Voice CLI is properly installed
check_installation() {
    log "Checking Voice CLI installation..."
    
    if ! command -v voice &> /dev/null; then
        error "Voice CLI is not installed or not in PATH"
        return 1
    fi
    
    # Check version
    local version=$(voice --version 2>/dev/null || echo "unknown")
    log "Voice CLI version: $version"
    
    # Check providers
    log "Checking available providers..."
    voice providers > /tmp/voice_providers.txt 2>&1 || true
    
    success "Voice CLI installation check completed"
}

# Function to run performance benchmarks
run_performance_benchmarks() {
    log "Running performance benchmarks..."
    
    cd "$PROJECT_ROOT"
    
    # Set environment variables
    export PYTHONDONTWRITEBYTECODE=1
    export TTS_MONITORING_MODE=1
    
    # Run different benchmark categories
    local benchmark_results=()
    
    # Basic synthesis benchmarks
    log "Running basic synthesis benchmarks..."
    if python -m pytest tests/e2e/test_performance_benchmarks.py::TestSynthesisPerformanceBenchmarks -v --tb=short; then
        benchmark_results+=("synthesis:PASS")
        success "Synthesis benchmarks completed"
    else
        benchmark_results+=("synthesis:FAIL")
        error "Synthesis benchmarks failed"
    fi
    
    # Provider comparison benchmarks
    log "Running provider comparison benchmarks..."
    if python -m pytest tests/e2e/test_performance_benchmarks.py::TestProviderPerformanceComparison -v --tb=short; then
        benchmark_results+=("provider_comparison:PASS")
        success "Provider comparison benchmarks completed"
    else
        benchmark_results+=("provider_comparison:FAIL")
        error "Provider comparison benchmarks failed"
    fi
    
    # Stress benchmarks (only if explicitly requested)
    if [[ "${RUN_STRESS_TESTS:-0}" == "1" ]]; then
        log "Running stress benchmarks..."
        export TEST_MEMORY_STRESS=1
        if python -m pytest tests/e2e/test_performance_benchmarks.py::TestStressAndScalabilityBenchmarks -v --tb=short; then
            benchmark_results+=("stress:PASS")
            success "Stress benchmarks completed"
        else
            benchmark_results+=("stress:FAIL")
            error "Stress benchmarks failed"
        fi
    fi
    
    # Regression detection
    log "Running performance regression detection..."
    if python -m pytest tests/e2e/test_performance_benchmarks.py::TestPerformanceRegression -v --tb=short; then
        benchmark_results+=("regression:PASS")
        success "Regression detection completed"
    else
        benchmark_results+=("regression:FAIL")
        error "Regression detection failed"
    fi
    
    # Summary
    local passed_count=0
    local total_count=${#benchmark_results[@]}
    
    log "Benchmark Results Summary:"
    for result in "${benchmark_results[@]}"; do
        local test_name="${result%:*}"
        local test_result="${result#*:}"
        
        if [[ "$test_result" == "PASS" ]]; then
            success "  $test_name: PASSED"
            ((passed_count++))
        else
            error "  $test_name: FAILED"
        fi
    done
    
    log "Overall: $passed_count/$total_count benchmarks passed"
    
    if [[ $passed_count -eq $total_count ]]; then
        success "All performance benchmarks passed!"
        return 0
    else
        warning "Some performance benchmarks failed"
        return 1
    fi
}

# Function to generate performance report
generate_performance_report() {
    log "Generating performance report..."
    
    local report_file="$PROJECT_ROOT/performance_report_$TIMESTAMP.md"
    local json_results="$RESULTS_DIR/latest_benchmark_results.json"
    
    # Create report header
    cat > "$report_file" << EOF
# TTS CLI Performance Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**System:** $(uname -a)
**Python:** $(python --version 2>&1)
**Voice Version:** $(voice --version 2>/dev/null || echo "unknown")

## Performance Benchmark Results

EOF
    
    # Parse JSON results if available
    if [[ -f "$json_results" ]]; then
        log "Processing benchmark results from $json_results"
        
        # Use Python to extract key metrics
        python3 << EOF >> "$report_file"
import json
import sys

try:
    with open("$json_results", "r") as f:
        results = json.load(f)
    
    print("### Synthesis Performance")
    if "short_text_synthesis" in results:
        sts = results["short_text_synthesis"]
        print(f"- Average synthesis time: {sts.get('avg_synthesis_time', 'N/A'):.2f}s")
        print(f"- Success rate: {sts.get('success_rate', 0) * 100:.1f}%")
        print(f"- Tests completed: {sts.get('test_count', 'N/A')}")
    
    print("\n### Provider Comparison")
    if "provider_comparison" in results:
        pc = results["provider_comparison"]
        print(f"- Providers tested: {len(pc.get('providers_tested', []))}")
        print(f"- Successful providers: {len(pc.get('successful_providers', []))}")
        if pc.get('fastest_provider'):
            print(f"- Fastest provider: {pc['fastest_provider']}")
    
    print("\n### Memory and Performance")
    if "memory_stress" in results:
        ms = results["memory_stress"]
        print(f"- Max memory usage: {ms.get('max_memory_usage', 'N/A'):.1f} MB")
        print(f"- Memory efficiency: {ms.get('memory_efficiency', 'N/A'):.1f} MB")
    
    if "concurrent_synthesis" in results:
        cs = results["concurrent_synthesis"]
        print(f"- Concurrent efficiency: {cs.get('concurrency_efficiency', 'N/A'):.1f}x")
        print(f"- Successful syntheses: {cs.get('successful_syntheses', 'N/A')}")
    
    print("\n### Performance Stability")
    if "performance_stability" in results:
        ps = results["performance_stability"]
        print(f"- Synthesis time CV: {ps.get('synthesis_time_cv', 'N/A'):.3f}")
        print(f"- RTF CV: {ps.get('rtf_cv', 'N/A'):.3f}")
        print(f"- Successful runs: {ps.get('successful_runs', 'N/A')}/{ps.get('run_count', 'N/A')}")

except Exception as e:
    print(f"Error processing results: {e}")
    sys.exit(1)
EOF
        
        success "Performance report generated: $report_file"
    else
        warning "No benchmark results found, generating basic report"
        echo "No detailed benchmark results available." >> "$report_file"
    fi
    
    # Add system information
    cat >> "$report_file" << EOF

## System Information

### CPU Information
\`\`\`
$(lscpu | head -20)
\`\`\`

### Memory Information
\`\`\`
$(free -h)
\`\`\`

### Disk Space
\`\`\`
$(df -h | head -10)
\`\`\`

### Python Packages
\`\`\`
$(pip list | grep -E "(voice|torch|numpy|scipy)" || echo "No relevant packages found")
\`\`\`

---
*Report generated by TTS CLI performance monitoring script*
EOF
    
    echo "$report_file"
}

# Function to upload results to monitoring service (placeholder)
upload_to_monitoring() {
    local report_file="$1"
    local json_results="$RESULTS_DIR/latest_benchmark_results.json"
    
    if [[ -z "${MONITORING_ENDPOINT:-}" ]]; then
        log "No monitoring endpoint configured, skipping upload"
        return 0
    fi
    
    log "Uploading results to monitoring service..."
    
    # Upload JSON results if available
    if [[ -f "$json_results" ]]; then
        if curl -X POST "$MONITORING_ENDPOINT/api/performance" \
               -H "Content-Type: application/json" \
               -H "Authorization: Bearer ${MONITORING_TOKEN:-}" \
               -d @"$json_results" \
               --connect-timeout 10 \
               --max-time 30; then
            success "Performance data uploaded successfully"
        else
            warning "Failed to upload performance data"
        fi
    fi
    
    # Upload report if monitoring supports it
    if [[ -f "$report_file" ]] && [[ -n "${MONITORING_REPORT_ENDPOINT:-}" ]]; then
        if curl -X POST "$MONITORING_REPORT_ENDPOINT" \
               -H "Content-Type: text/markdown" \
               -H "Authorization: Bearer ${MONITORING_TOKEN:-}" \
               --data-binary @"$report_file" \
               --connect-timeout 10 \
               --max-time 30; then
            success "Performance report uploaded successfully"
        else
            warning "Failed to upload performance report"
        fi
    fi
}

# Function to check for performance regressions
check_regressions() {
    log "Checking for performance regressions..."
    
    local baselines_file="$RESULTS_DIR/performance_baselines.json"
    local current_results="$RESULTS_DIR/latest_benchmark_results.json"
    
    if [[ ! -f "$baselines_file" ]]; then
        warning "No performance baselines found, cannot check for regressions"
        return 0
    fi
    
    if [[ ! -f "$current_results" ]]; then
        error "No current results found for regression analysis"
        return 1
    fi
    
    # Use Python to compare results
    python3 << EOF
import json
import sys

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

baselines = load_json("$baselines_file")
current = load_json("$current_results")

if not baselines or not current:
    sys.exit(1)

regressions = []
improvements = []

# Check key performance metrics
metrics_to_check = [
    ("short_text_synthesis", "avg_synthesis_time", "lower_is_better"),
    ("medium_text_synthesis", "synthesis_time", "lower_is_better"),
    ("provider_comparison", "fastest_provider_time", "lower_is_better"),
]

for test_name, metric_name, direction in metrics_to_check:
    if test_name in baselines and test_name in current:
        baseline_val = baselines[test_name].get(metric_name)
        current_val = current[test_name].get(metric_name)
        
        if baseline_val is not None and current_val is not None:
            change_percent = ((current_val - baseline_val) / baseline_val) * 100
            
            if direction == "lower_is_better":
                if change_percent > 20:  # 20% slower
                    regressions.append(f"{test_name}.{metric_name}: {change_percent:.1f}% slower")
                elif change_percent < -10:  # 10% faster
                    improvements.append(f"{test_name}.{metric_name}: {abs(change_percent):.1f}% faster")
            else:  # higher_is_better
                if change_percent < -20:  # 20% worse
                    regressions.append(f"{test_name}.{metric_name}: {abs(change_percent):.1f}% worse")
                elif change_percent > 10:  # 10% better
                    improvements.append(f"{test_name}.{metric_name}: {change_percent:.1f}% better")

if regressions:
    print("REGRESSIONS DETECTED:")
    for regression in regressions:
        print(f"  - {regression}")
    sys.exit(2)
elif improvements:
    print("PERFORMANCE IMPROVEMENTS:")
    for improvement in improvements:
        print(f"  + {improvement}")
    sys.exit(0)
else:
    print("No significant performance changes detected")
    sys.exit(0)
EOF
    
    local exit_code=$?
    
    case $exit_code in
        0)
            success "No significant performance changes detected"
            ;;
        1)
            error "Failed to analyze performance regression"
            return 1
            ;;
        2)
            error "Performance regressions detected!"
            return 2
            ;;
    esac
}

# Function to cleanup old results
cleanup_old_results() {
    log "Cleaning up old performance results..."
    
    # Keep last 30 days of results
    find "$PROJECT_ROOT" -name "performance_report_*.md" -mtime +30 -delete 2>/dev/null || true
    find "$PROJECT_ROOT/logs" -name "performance_monitoring.log.*" -mtime +30 -delete 2>/dev/null || true
    
    # Rotate monitoring log if it's too large (>10MB)
    if [[ -f "$MONITORING_LOG" ]] && [[ $(stat -f%z "$MONITORING_LOG" 2>/dev/null || stat -c%s "$MONITORING_LOG" 2>/dev/null || echo 0) -gt 10485760 ]]; then
        mv "$MONITORING_LOG" "$MONITORING_LOG.$(date +%Y%m%d_%H%M%S)"
        touch "$MONITORING_LOG"
        log "Rotated monitoring log"
    fi
    
    success "Cleanup completed"
}

# Main execution function
main() {
    log "Starting TTS CLI performance monitoring"
    log "Timestamp: $TIMESTAMP"
    
    local exit_code=0
    
    # Check installation
    if ! check_installation; then
        error "Installation check failed"
        exit 1
    fi
    
    # Run performance benchmarks
    if ! run_performance_benchmarks; then
        warning "Some performance benchmarks failed"
        exit_code=1
    fi
    
    # Generate performance report
    local report_file
    if report_file=$(generate_performance_report); then
        log "Performance report: $report_file"
    else
        error "Failed to generate performance report"
        exit_code=1
    fi
    
    # Check for regressions
    if ! check_regressions; then
        local regression_exit=$?
        if [[ $regression_exit -eq 2 ]]; then
            error "Performance regressions detected!"
            exit_code=2
        else
            warning "Regression analysis failed"
            exit_code=1
        fi
    fi
    
    # Upload to monitoring service if configured
    if [[ -n "$report_file" ]]; then
        upload_to_monitoring "$report_file"
    fi
    
    # Cleanup
    cleanup_old_results
    
    log "Performance monitoring completed with exit code: $exit_code"
    
    if [[ $exit_code -eq 0 ]]; then
        success "All performance checks passed!"
    elif [[ $exit_code -eq 1 ]]; then
        warning "Performance monitoring completed with warnings"
    else
        error "Performance monitoring detected critical issues"
    fi
    
    exit $exit_code
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "TTS CLI Performance Monitoring Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --stress           Run stress tests in addition to normal benchmarks"
        echo "  --quick            Run only basic benchmarks (faster execution)"
        echo ""
        echo "Environment Variables:"
        echo "  MONITORING_ENDPOINT      API endpoint for uploading results"
        echo "  MONITORING_TOKEN         Authentication token for monitoring service"
        echo "  MONITORING_REPORT_ENDPOINT  Endpoint for uploading markdown reports"
        echo "  RUN_STRESS_TESTS         Set to 1 to run stress tests"
        echo ""
        echo "Examples:"
        echo "  $0                      # Run standard performance monitoring"
        echo "  $0 --stress             # Run with stress tests"
        echo "  RUN_STRESS_TESTS=1 $0   # Run with stress tests via environment"
        exit 0
        ;;
    --stress)
        export RUN_STRESS_TESTS=1
        ;;
    --quick)
        export QUICK_MODE=1
        ;;
    "")
        # No arguments, run normally
        ;;
    *)
        error "Unknown argument: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

# Run main function
main
