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

## 🚦 Implementation Timeline

### Immediate Wins (1-2 days)
- [ ] Add @provider shortcut parsing with validation
- [ ] Remove legacy flags (-l, --list) entirely  
- [ ] Add `tts providers` command (rename from `tts models`)
- [ ] Implement option precedence warnings for conflicts
- [ ] Update error messages to reference new syntax

### Medium Term (1 week)
- [ ] Add `tts save` subcommand (alongside --save)
- [ ] Add `tts document` subcommand (alongside --document)
- [ ] Add `tts voice` subcommand group
- [ ] Enhanced help text and error messages
- [ ] Comprehensive tab completion

### Long Term (1-2 months)
- [ ] Deprecation warnings for old syntax
- [ ] Migration guide and tooling
- [ ] Performance optimization
- [ ] Community feedback integration

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