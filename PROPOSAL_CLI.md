# TTS CLI v2.0 - Complete Design Proposal

## 🎯 Executive Summary

This proposal outlines a comprehensive redesign of the TTS CLI to address consistency issues, improve discoverability, and enhance user experience while maintaining full backward compatibility. The design introduces intuitive provider shortcuts, reorganizes commands into logical subcommands, and provides a smooth migration path for existing users.

## 🔍 Current Problems

### 1. Inconsistent Command Structure
- **Mixed paradigms**: Some features use subcommands (`tts voices`), others use flags (`tts --document`)
- **Unclear intent**: `tts "text" --save` doesn't clearly express "save audio to file"
- **Poor discoverability**: Users can't easily discover what options are available for each provider

### 2. Verbose Provider Selection
- **Current**: `tts "text" --model edge_tts` (long and forgettable)
- **Provider names**: Some are technical (`edge_tts` vs just `edge`)

### 3. Complex Document Processing
- **Too many flags**: `tts --document file.md --emotion-profile marketing --ssml-platform google --save`
- **Inconsistent with subcommand pattern**

## 🚀 Proposed Solution

### Core Design Principles
1. **Consistency**: All major features use subcommands
2. **Simplicity**: Common tasks remain simple
3. **Discoverability**: Clear help and intuitive shortcuts
4. **Backward Compatibility**: Existing commands continue working
5. **Progressive Enhancement**: Users can adopt new syntax incrementally

## 📋 New Command Structure

### 🎤 Core Speech Commands

#### Basic Speech (Unchanged)
```bash
tts "text"                                    # Stream to speakers (default)
echo "text" | tts                             # Read from stdin
```

#### Explicit Save Command (New)
```bash
tts save "text"                               # Save to default location
tts save "text" -o output.mp3                # Save to specific file
tts save "text" --format wav                 # Save with format
```

#### Document Processing (New Subcommand)
```bash
tts document file.html                        # Process HTML document
tts document file.md                          # Process Markdown
tts document file.json                        # Process JSON
tts document file.html --save                 # Save document audio
tts document file.md --emotion marketing      # Marketing emotion style
tts document file.html --ssml google         # Generate Google SSML
```

### 🚀 Provider Shortcuts (New @syntax)

#### Basic Provider Usage
```bash
tts @edge "text"                              # Use Edge TTS
tts @openai "text"                            # Use OpenAI TTS
tts @elevenlabs "text"                        # Use ElevenLabs
tts @google "text"                            # Use Google TTS
tts @chatterbox "text"                        # Use Chatterbox
```

#### Provider + Options (Enhanced key=value)
```bash
tts @edge "text" voice=en-US-JennyNeural      # Edge TTS with voice
tts @elevenlabs "text" voice=rachel stability=0.75 similarity_boost=0.85
tts @google "text" voice=en-US-Neural2-A speaking_rate=1.25
tts @chatterbox "text" voice=/path/to/voice.wav exaggeration=0.7
```

#### Provider + Commands
```bash
tts save @edge "text"                         # Save with Edge TTS
tts save @openai "text" --rate +50%           # Save OpenAI with rate adjustment
tts document file.html @elevenlabs            # Process with ElevenLabs
tts document file.md @google --emotion technical  # Google with emotion
```

### 🎵 Global Speech Options

#### Rate and Pitch (CLI Flags)
```bash
tts "text" --rate +50%                        # Increase speech rate
tts "text" --pitch +10Hz                      # Increase pitch
tts save "text" --rate +75%                   # Save with fast rate
tts @edge "text" --rate +50%                  # Provider + rate
```

#### Output Formats
```bash
tts save "text" --format mp3                  # MP3 output
tts save "text" --format wav                  # WAV output
tts save "text" -f ogg                        # Short format flag
```

### 🎭 Voice Management (Reorganized)

#### Voice Operations (New Structure)
```bash
tts voices                                    # Interactive browser (unchanged)
tts voice load voice.wav                      # Load voice file
tts voice unload voice.wav                    # Unload specific voice
tts voice unload --all                        # Unload all voices
tts voice status                              # Show loaded voices only
```

### 🔧 Provider and System Commands

#### Provider Information (Enhanced)
```bash
tts providers                                 # List all providers (renamed)
tts info                                      # Show providers with descriptions
tts info edge_tts                            # Detailed Edge TTS information
tts info @edge                               # Alternative with shortcut
```

#### System Commands
```bash
tts status                                    # Full system status
tts doctor                                    # System diagnostics
tts install chatterbox                       # Install dependencies
```

### ⚙️ Configuration (Unchanged)
```bash
tts config                                   # Show configuration
tts config voice edge_tts:en-US-JennyNeural  # Set default voice
tts config rate +25%                         # Set default rate
tts config google_api_key YOUR_KEY           # Set API keys
```

## 🔄 Backward Compatibility Strategy

### Complete Command Mapping Table

| Current Command | New Command | Status | Notes |
|----------------|-------------|---------|-------|
| `tts "text"` | `tts "text"` | ✅ Unchanged | Default streaming behavior preserved |
| `tts "text" --save` | `tts save "text"` | 🔄 Both work | New syntax preferred |
| `tts "text" --model edge_tts` | `tts @edge "text"` | 🔄 Both work | Much shorter syntax |
| `tts --document file.html` | `tts document file.html` | 🔄 Both work | Consistent subcommand |
| `tts load voice.wav` | `tts voice load voice.wav` | 🔄 Both work | Grouped under voice |
| `tts unload voice.wav` | `tts voice unload voice.wav` | 🔄 Both work | Grouped under voice |
| `tts models` | `tts providers` | 🔄 Both work | Better naming |
| `tts -l` / `tts --list` | `tts providers` | ❌ Removed | Legacy cleanup |
| `tts unload all` | `tts voice unload --all` | 🔄 Standardized | Consistent flag syntax |

### Phase 1: Additive Changes (v2.0)
- **Add new syntax** alongside existing commands
- **No breaking changes** - all current commands continue working
- **Internal mapping** - old syntax maps to new implementation

```bash
# Both work identically
tts "text" --model edge_tts                  # Current syntax
tts @edge "text"                             # New syntax

tts "text" --save                            # Current syntax  
tts save "text"                              # New syntax

tts --document file.html                     # Current syntax
tts document file.html                       # New syntax
```

### Phase 2: Deprecation Warnings (v2.1)
- **Add warnings** for old syntax
- **Continue working** but inform users of new syntax
- **Update documentation** to show new patterns

```bash
$ tts "text" --save
⚠️  Deprecation: Use 'tts save "text"' instead (--save flag will be removed in v3.0)
[audio plays normally]
```

### Phase 3: Remove Old Syntax (v3.0)
- **Remove deprecated flags** after sufficient notice period
- **Keep core compatibility** for basic usage patterns

## 🎯 Implementation Details

### Provider Shortcut Mapping
```python
PROVIDER_SHORTCUTS = {
    "edge": "edge_tts",
    "openai": "openai", 
    "elevenlabs": "elevenlabs",
    "google": "google", 
    "chatterbox": "chatterbox"
}
```

### Option Precedence Rules
1. **CLI flags** (--rate +50%)
2. **Key=value options** (rate=+25%)
3. **Configuration defaults**

**Conflict handling:**
```bash
$ tts @edge "text" --rate +100% rate=+75%
⚠️  Both --rate and rate= specified. Using --rate +100%
```

### Command Parsing Logic
```python
def parse_command(args):
    provider = None
    
    # Check for @provider shortcuts anywhere in args
    for i, arg in enumerate(args):
        if arg.startswith('@'):
            shortcut = arg[1:]
            provider = PROVIDER_SHORTCUTS.get(shortcut)
            if not provider:
                error(f"Unknown provider shortcut: @{shortcut}")
                show_available_providers()
            args.pop(i)  # Remove @provider from args
            break
    
    # Handle subcommands first
    if args[0] in ['save', 'document', 'voice', 'providers', 'info']:
        return handle_subcommand(args, provider=provider)
    
    # Map old syntax to new internally for backward compatibility
    if hasattr(args, 'save') and args.save and args.text:
        return handle_save_command(args.text, provider=provider)
    
    if hasattr(args, 'document') and args.document:
        return handle_document_command(args.document, provider=provider)
    
    # Default: streaming synthesis
    return handle_speak_command(args[0], provider=provider)
```

## 📚 Help System Updates

### Enhanced Help Structure
```bash
tts --help                    # Main help showing new structure
tts save --help               # Subcommand-specific help
tts @edge --help              # Provider-specific help
tts help migration            # Migration guide
```

### Provider Discovery
```bash
$ tts info @elevenlabs
🎤 ElevenLabs
   Premium voice cloning with advanced features

📋 Available Options:
   voice=Voice to use (e.g., rachel)
   stability=Voice stability (0.0-1.0, default: 0.5)
   similarity_boost=Voice similarity boost (0.0-1.0, default: 0.5)
   style=Style exaggeration (0.0-1.0, default: 0.0)

💡 Usage Examples:
   tts @elevenlabs "Hello world"
   tts @elevenlabs "text" voice=rachel stability=0.75
```

## 🚦 Implementation Timeline & Testing Strategy

### Phase 1: Foundation & Real Testing (v2.0) - 1 week

#### Implementation
- [ ] Add @provider shortcut parsing with validation
- [ ] Add `tts save` subcommand (alongside --save)
- [ ] Add `tts document` subcommand (alongside --document)
- [ ] Add `tts voice` subcommand group
- [ ] Add `tts providers` command (rename from `tts models`)
- [ ] Implement option precedence warnings for conflicts

#### Real Testing Strategy (No Mocks)
```bash
# Test actual command execution and file outputs
./test.sh phase1                           # Run Phase 1 test suite

# 1. Command Parity Tests - Both syntaxes produce identical results
tts "hello world" --save -o old.wav
tts save "hello world" -o new.wav
diff old.wav new.wav                       # Must be identical

tts "text" --model edge_tts --save -o old.wav  
tts save @edge "text" -o new.wav
diff old.wav new.wav                       # Must be identical

# 2. Provider Shortcut Tests - Real provider calls
tts @edge "test" --save -o edge.wav        # Must create valid audio
tts @openai "test" --save -o openai.wav    # Must create valid audio (if API key set)
file edge.wav openai.wav                   # Verify actual audio files

# 3. Document Processing Tests - Real file processing  
echo "# Test" > test.md
tts document test.md --save -o doc.wav     # Process real markdown
tts --document test.md --save -o old_doc.wav  # Old syntax
diff doc.wav old_doc.wav                   # Must be identical

# 4. Error Handling Tests - Real error conditions
tts @invalid "text" 2>&1 | grep "Unknown provider"  # Must show proper error
tts save "text" -o /invalid/path.wav 2>&1 | grep -i "permission\|error"

# 5. Voice Commands Tests - Real voice operations
cp /path/to/test/voice.wav test_voice.wav
tts voice load test_voice.wav              # Must load successfully
tts voice status | grep test_voice.wav     # Must show in status
tts voice unload test_voice.wav            # Must unload
tts voice status | grep -v test_voice.wav  # Must not show in status
```

#### Phase 1 Completion Criteria
- [ ] ✅ All command pairs produce bit-identical output files
- [ ] ✅ All provider shortcuts work with real providers 
- [ ] ✅ Error messages reference new syntax appropriately
- [ ] ✅ Help system updated and functional
- [ ] ✅ Performance within 5% of baseline (time actual commands)
- [ ] ✅ Zero regressions in existing functionality

#### Phase 1 Cleanup
- [ ] Remove duplicate code paths where possible
- [ ] Consolidate command handlers internally
- [ ] Update internal documentation
- [ ] Archive old test cases that are now redundant

### Phase 1.5: Validation & Metrics (v2.0.1) - 3 days

#### Real Usage Analysis
```bash
# Add telemetry to track real usage patterns (opt-in)
tts config telemetry enable               # Optional usage tracking

# Analyze which commands users actually run
grep "old syntax used" logs/tts.log | wc -l   # Track old syntax usage
grep "new syntax used" logs/tts.log | wc -l   # Track new syntax adoption
```

#### Performance Testing
```bash
# Real performance benchmarks - no synthetic tests
time tts "long text here..." --save -o old.wav     # Baseline timing
time tts save "long text here..." -o new.wav       # New syntax timing
# New syntax must be within 5% of old syntax

# Memory usage testing
/usr/bin/time -v tts save @edge "text" -o test.wav 2>&1 | grep "Maximum resident"
```

#### Phase 1.5 Completion Criteria  
- [ ] ✅ Usage metrics collected from real users
- [ ] ✅ Performance regressions fixed
- [ ] ✅ Critical bugs resolved
- [ ] ✅ Documentation gaps filled

### Phase 2: Deprecation & Migration (v2.1) - 2 weeks

#### Implementation
- [ ] Add deprecation warnings for old syntax
- [ ] Create migration scanner tool
- [ ] Update all documentation to show new syntax first
- [ ] Add migration helpers

#### Real Migration Testing
```bash
# Test actual user scripts and workflows
./test.sh migration                        # Run migration test suite

# 1. Migration Tool Tests - Real script scanning
echo 'tts "hello" --save' > old_script.sh
tts migrate --check old_script.sh          # Must detect old syntax
tts migrate --convert old_script.sh > new_script.sh  # Auto-convert
bash new_script.sh                         # Must work identically

# 2. Warning System Tests - Real deprecation warnings  
tts "text" --save 2>&1 | grep -i "deprecat"     # Must show warning
tts save "text" 2>&1 | grep -v "deprecat"       # Must not show warning

# 3. Help System Tests - Real help output prioritizes new syntax
tts --help | head -20 | grep -c "@"             # New syntax examples prominent
tts save --help | grep -c "save"                # Subcommand help works
```

#### Phase 2 Completion Criteria
- [ ] ✅ <20% of commands use old syntax (real telemetry data)
- [ ] ✅ Migration tool tested on 50+ real user scripts
- [ ] ✅ All documentation updated and verified
- [ ] ✅ Community feedback addressed
- [ ] ✅ Zero critical bugs in deprecation system

#### Phase 2 Cleanup  
- [ ] Remove redundant internal command paths
- [ ] Simplify option parsing logic
- [ ] Clean up test suites (remove old syntax tests)
- [ ] Update CI/CD to focus on new syntax

### Phase 3: Legacy Removal & Final Cleanup (v3.0) - 1 week

#### Implementation
- [ ] Remove all deprecated flags and options
- [ ] Remove old command parsing paths  
- [ ] Remove deprecation warning system
- [ ] Final code consolidation

#### Real Cleanup Testing
```bash
# Test that old syntax is completely removed
./test.sh cleanup                          # Run cleanup verification

# 1. Old Syntax Rejection Tests - Must fail cleanly
tts "text" --save 2>&1 | grep -i "unknown.*option"   # Must reject --save
tts --document file.html 2>&1 | grep -i "unknown"    # Must reject --document
tts -l 2>&1 | grep -i "unknown"                       # Must reject -l

# 2. Codebase Cleanup Verification - No legacy references
grep -r "save.*flag" tts_cli/ && exit 1               # No --save references
grep -r "document.*flag" tts_cli/ && exit 1           # No --document references  
grep -r "models.*command" tts_cli/ && exit 1          # No old "models" command

# 3. Documentation Cleanup - No old syntax examples
grep -r "\-\-save" docs/ README.md && exit 1          # No --save in docs
grep -r "\-\-document" docs/ README.md && exit 1      # No --document in docs
grep -r "tts models" docs/ README.md && exit 1        # No old models command

# 4. Final Integration Tests - Real end-to-end workflows
tts save @edge "hello world" -o final_test.wav        # Core functionality works
tts document README.md @google --save                  # Document processing works
tts voice load test.wav && tts voice status           # Voice management works
```

#### Phase 3 Completion Criteria
- [ ] ✅ Codebase 25%+ smaller (measured lines of code)
- [ ] ✅ Zero references to old syntax in code/docs/tests
- [ ] ✅ All functionality accessible through new syntax only
- [ ] ✅ Performance improved by 10%+ (measured on real commands)
- [ ] ✅ Test suite 100% focused on new syntax
- [ ] ✅ Documentation completely updated

#### Phase 3 Final Cleanup
- [ ] Remove all deprecation-related code
- [ ] Archive old documentation versions
- [ ] Remove legacy test files and fixtures
- [ ] Final performance optimization pass
- [ ] Update changelog with breaking changes summary

### Testing Infrastructure Requirements

#### Real Test Environment Setup
```bash
# Tests must run against real providers when available
export OPENAI_API_KEY="${OPENAI_API_KEY:-skip}"       # Skip if no key
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-skip}"       # Skip if no key
export ELEVENLABS_API_KEY="${ELEVENLABS_API_KEY:-skip}" # Skip if no key

# Always test Edge TTS (free, no API key required)
# Always test Chatterbox (local, no API required)
# Test others only when API keys available

# Create real test fixtures
mkdir -p test_fixtures/
echo "Test content" > test_fixtures/test.txt
echo "# Markdown Test" > test_fixtures/test.md
echo '{"text": "JSON test"}' > test_fixtures/test.json
```

#### Success Metrics - Real Data Only
- **File size comparisons**: `diff` and `wc -c` on actual audio files
- **Performance timing**: `time` command on real TTS operations  
- **Memory usage**: `/usr/bin/time -v` on actual command execution
- **Error rate**: Count actual failed commands vs successful ones
- **Usage analytics**: Real telemetry from opt-in users only

## 🎯 Benefits Summary

### For New Users
- **Intuitive**: `tts @edge "text"` is immediately understandable
- **Discoverable**: `tts info @provider` shows all options
- **Consistent**: All major features use subcommands

### For Existing Users
- **No disruption**: Current commands continue working
- **Gradual migration**: Can adopt new syntax over time
- **Clear path**: Deprecation warnings guide migration

### For Developers
- **Cleaner codebase**: Consistent command structure
- **Easier maintenance**: Logical organization
- **Better testing**: Clear separation of concerns

## 🔍 Edge Cases and Considerations

### Provider Shortcut Conflicts
- **Reserved names**: Avoid shortcuts that conflict with shell commands
- **Validation**: Clear error messages for unknown shortcuts
- **Documentation**: Maintain shortcut registry

### Error Messages
```bash
$ tts @invalid "text"
Error: Unknown provider '@invalid'
Available providers: @edge, @openai, @elevenlabs, @google, @chatterbox
Use 'tts providers' to see detailed information.
```

### Tab Completion
```bash
tts @<TAB>                    # Shows: edge, openai, elevenlabs, google, chatterbox
tts document <TAB>            # Shows: *.html, *.md, *.json files in current directory
tts save @<TAB>               # Shows: edge, openai, elevenlabs, google, chatterbox
tts info @<TAB>               # Shows: edge, openai, elevenlabs, google, chatterbox
tts @edge voice=<TAB>         # Shows: available Edge TTS voices (requires API call)
tts @elevenlabs voice=<TAB>   # Shows: rachel, domi, bella, antoni, elli (cached)
```

## 🏆 Success Metrics

### User Experience
- **Reduced command length** for common operations
- **Faster onboarding** for new users
- **Improved discoverability** of features

### Technical
- **Cleaner codebase** organization
- **Better test coverage** through clear separation
- **Easier feature addition** with consistent patterns

### Adoption
- **Gradual migration** without breaking existing workflows
- **Community feedback** integration
- **Documentation clarity** improvement

## 📝 Migration Guide

### For Script Authors
```bash
# Old script.sh
tts "Hello" --model edge_tts --save -o output.mp3

# New script.sh (Phase 1 - both work)
tts save @edge "Hello" -o output.mp3

# Migration tool
tts migrate --check script.sh          # Check for old syntax
tts migrate --convert script.sh        # Auto-convert to new syntax
```

### For End Users
1. **Learn shortcuts**: `@edge` instead of `--model edge_tts`
2. **Use subcommands**: `tts save` instead of `tts --save`
3. **Explore options**: `tts info @provider` for available settings

## 🎉 Conclusion

This proposal addresses the core usability issues in the current TTS CLI while maintaining full backward compatibility. The new structure is more intuitive, discoverable, and consistent, while the implementation strategy ensures a smooth transition for all users.

The @provider shortcuts alone will dramatically improve daily usability, while the reorganized subcommand structure provides a solid foundation for future feature development.

**Next Steps**: Begin Phase 1 implementation with @provider shortcuts and enhanced help system, gathering community feedback throughout the process.