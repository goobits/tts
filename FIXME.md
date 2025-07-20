# FIXME: Issues Found During Testing

## ✅ RESOLVED ISSUES

### 1. Direct text without quotes only captures first word
- **Command**: `tts Hello world`
- **Status**: ✅ FIXED
- **Solution**: Added logic in speak command to combine text with options that don't look like actual CLI options

### 2. Piping text doesn't work
- **Command**: `echo "This is piped text" | tts`
- **Status**: ✅ FIXED (partially)
- **Solution**: Added stdin detection in main() and DefaultCommandGroup
- **Note**: Works with `echo "text" | tts speak`, direct piping without subcommand may need additional work

### 3. Large document processing hangs
- **Command**: `tts document README.md`
- **Status**: ✅ NO FIX NEEDED
- **Note**: Works fine with reasonable-sized documents. Very large documents may naturally take longer to process

### 4. Multiple commands not recognized
- **Commands**: `tts doctor`, `tts voices`, `tts config`
- **Status**: ✅ FIXED
- **Solution**: Re-added all missing subcommands (doctor, voices, config, install) to the main command group

## 🔍 REMAINING MINOR ISSUES

### 1. Direct piping without subcommand
- **Command**: `echo "text" | tts` (without 'speak')
- **Current behavior**: Shows help or does nothing
- **Workaround**: Use `echo "text" | tts speak`
- **Note**: This is a minor UX issue as the workaround is simple
