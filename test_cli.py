#!/usr/bin/env python3

import os
import tempfile

from click.testing import CliRunner

from src.tts.cli import main

runner = CliRunner()

# Test synthesis
with tempfile.TemporaryDirectory() as tmpdir:
    output_file = os.path.join(tmpdir, 'test.mp3')
    result = runner.invoke(main, ['save', '@edge', 'test synthesis', '-o', output_file])
    print('Synthesis Exit code:', result.exit_code)
    print('Synthesis Output:', result.output)

    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f'Output file exists: {output_file}, size: {file_size} bytes')

        # Test audio validation
        import sys
        from pathlib import Path
        sys.path.append('/workspace/tts/tests/utils')
        from test_helpers import validate_audio_file_comprehensive

        validation_result = validate_audio_file_comprehensive(
            Path(output_file),
            expected_format="mp3",
            min_duration=1.0,
            max_duration=10.0,
            min_file_size=500
        )

        print(f'Validation result: valid={validation_result.valid}')
        if not validation_result.valid:
            print(f'Validation error: {validation_result.error}')
    else:
        print('Output file not created')

    if result.exit_code != 0:
        print('Exception:', result.exception)
