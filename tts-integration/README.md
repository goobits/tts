# TTS Integration Components

This directory contains all Text-to-Speech (TTS) related components that were extracted from the GOOBITS STT codebase to maintain separation between STT and TTS functionality.

## Extracted Components

### 🗂️ **Modules Moved Here**

#### `speech_synthesis/`
Complete TTS pipeline with emotion detection and SSML generation:
- `emotion_detector.py` - Basic emotion detection for TTS
- `advanced_emotion_detector.py` - Document-aware emotion detection  
- `semantic_formatter.py` - Format semantic elements for speech
- `speech_markdown.py` - Convert elements to Speech Markdown syntax
- `ssml_generator.py` - Platform-specific SSML generation (Azure, Google, Amazon)
- `tts_engine.py` - Text-to-speech engine integration

#### `document_parsing/`
Document processing for TTS applications:
- `base_parser.py` - Base classes and semantic element definitions
- `markdown_parser.py` - Enhanced markdown parsing with semantic elements
- `parser_factory.py` - Markdown-first architecture parser factory
- `performance_cache.py` - Document caching system (renamed from document_cache.py)
- `universal_converter.py` - HTML/JSON to markdown conversion

#### `integration/` 
Cross-cutting TTS orchestration:
- `mixed_content_processor.py` - Handle documents vs transcriptions intelligently

### 📄 **Files Moved Here**

#### CLI Implementation
- `main_tts.py` - Original main.py with full TTS CLI integration
- `main_with_tts.py` - Copy of main.py before TTS removal

#### Documentation
- `PROPOSAL.md` - Original multi-format document-to-speech proposal
- `PIVOT_PLAN.md` - Phase 3.5 markdown-first architecture pivot
- `PROPOSAL_MIGRATION.md` - Directory structure migration proposal

## 🔧 **TTS Features Removed from STT main.py**

### CLI Options Removed
```python
# These CLI options were removed from STT main.py:
@click.option("--document", metavar="FILE", help="📄 Convert document to speech (markdown, HTML, JSON)")
@click.option("--format", type=click.Choice(['auto', 'markdown', 'html', 'json']), 
              default='auto', help="🎯 Document format (auto-detect by default)")
@click.option("--ssml-platform", type=click.Choice(['azure', 'google', 'amazon', 'generic']),
              default='generic', help="🎤 SSML platform for voice synthesis")
@click.option("--emotion-profile", type=click.Choice(['technical', 'marketing', 'narrative', 'tutorial', 'auto']),
              default='auto', help="🎭 Emotion profile for document type")
@click.option("--cache", is_flag=True, help="💾 Enable document caching for performance")
@click.option("--mixed-mode", is_flag=True, help="🔄 Enable mixed content processing")
```

### Function Removed
- `handle_document_command(args)` - Complete 200+ line TTS document processing function

### Argument Processing Removed
```python
# These arguments were removed from main() function signatures:
document, format, ssml_platform, emotion_profile, cache, mixed_mode

# These were removed from args object:
document=document,
document_format=format,
ssml_platform=ssml_platform,
emotion_profile=emotion_profile,
cache=cache,
mixed_mode=mixed_mode
```

## 🎯 **Architecture Overview**

The TTS system implements a **markdown-first architecture** where:

1. **Universal Conversion**: HTML/JSON → Markdown via `universal_converter.py`
2. **Semantic Parsing**: Markdown → Semantic Elements via `markdown_parser.py`  
3. **Emotion Detection**: Elements → Emotion Analysis via `advanced_emotion_detector.py`
4. **Speech Formatting**: Elements → Speech Markdown via `speech_markdown.py`
5. **SSML Generation**: Speech Markdown → Platform SSML via `ssml_generator.py`
6. **TTS Output**: SSML → Speech via `tts_engine.py`

## 🔄 **Integration Instructions**

### To integrate these TTS components into another project:

1. **Copy modules** to your TTS project directory structure
2. **Update import paths** in `main_tts.py` to match your project structure
3. **Install dependencies**:
   ```bash
   # Core TTS dependencies
   pip install faster-whisper torch
   pip install spacy deepmultilingualpunctuation  # For advanced text processing
   pip install opuslib websockets  # If using audio streaming
   ```

4. **Merge CLI options** from `main_tts.py` into your main CLI
5. **Test document processing**:
   ```bash
   python main_tts.py --document test.html --format html --json
   python main_tts.py --document test.json --format json --ssml-platform azure
   ```

### Key Dependencies
- **Document parsing**: No external deps (regex-based conversion)
- **Speech synthesis**: espeak, festival, or cloud TTS APIs
- **SSML generation**: Built-in (no external deps)
- **Emotion detection**: spacy (optional, has fallbacks)
- **Performance caching**: Built-in pickle-based system

## 📊 **Performance Characteristics**

### Code Reduction Achieved
- **Before**: 383 lines across 3 separate parsers (HTML, JSON, Markdown)
- **After**: 221 lines with universal converter + markdown parser
- **Reduction**: 42% code reduction while improving functionality

### Features Supported
- ✅ **Multi-format input**: HTML, JSON, Markdown, plain text
- ✅ **Emotion detection**: Technical, marketing, narrative, tutorial profiles  
- ✅ **SSML generation**: Azure, Google, Amazon platform support
- ✅ **Performance caching**: Document processing optimization
- ✅ **Mixed content**: Handle both documents and transcriptions

## 🧪 **Test Files**

Test fixtures are available in the STT project's `tests/fixtures/` directory:
- HTML documents: `test*.html`
- JSON documents: `test*.json` 
- Markdown documents: `test*.md`
- Demo scripts: `demo_document_speech.py`

## 📝 **Notes**

- **Separation rationale**: STT = Speech→Text, TTS = Text→Speech. These are fundamentally different pipelines.
- **Architecture quality**: The TTS system is production-ready with comprehensive emotion detection and SSML support.
- **Integration path**: Copy components and adapt import paths for your TTS project structure.
- **Maintained compatibility**: The markdown-first architecture is extensible for additional document formats.

---

**Original context**: These components were built as part of a "document-to-speech" feature that was misinterpreted as TTS rather than STT. The implementation is high-quality and ready for TTS applications.