# Multi-Format Document-to-Speech System

## Overview

Extend GOOBITS STT with intelligent document parsing and TTS formatting to enable natural-sounding speech synthesis from various document formats (Markdown, HTML, JSON, etc.) with appropriate timing, emphasis, and emotional expression.

## Architecture

### New Module Structure
```
src/
├── text_formatting/          # Existing transcription processing (unchanged)
├── document_parsing/          # New: Multi-format document parsing
│   ├── __init__.py
│   ├── base_parser.py        # Abstract parser interface
│   ├── markdown_parser.py    # Markdown → semantic structure
│   ├── html_parser.py        # HTML → semantic structure  
│   ├── json_parser.py        # JSON → readable text
│   └── parser_factory.py     # Format detection & parser selection
└── speech_synthesis/          # New: TTS-specific formatting
    ├── __init__.py
    ├── semantic_formatter.py  # Semantic structure → TTS markup
    ├── emotion_detector.py    # Content-based emotion analysis
    ├── ssml_generator.py      # Generate SSML from markup
    └── speech_markdown.py     # Speech Markdown support
```

### Data Flow
```
Document Input → document_parsing/ → Semantic Structure → speech_synthesis/ → TTS Engine
```

## Key Components

### 1. Document Parsing (`src/document_parsing/`)

**`base_parser.py`**
```python
@dataclass
class SemanticElement:
    type: str  # 'heading', 'bold', 'code', 'list_item', etc.
    content: str
    level: Optional[int] = None  # For headings
    metadata: Dict = field(default_factory=dict)

class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> List[SemanticElement]:
        pass
```

**`markdown_parser.py`**
- Parse headers (# → H1, ## → H2) → pitch/pace changes
- **Bold** → emphasis/louder speech
- *Italic* → softer tone
- `code` → monotone voice
- Lists → automatic pauses
- Links → "link to..." announcements

**`html_parser.py`**
- Extract semantic meaning from HTML tags
- `<h1>` → heading tone, `<strong>` → emphasis
- Strip formatting, preserve structure

**`json_parser.py`**
- Convert structured data to natural language
- Arrays → lists with pauses
- Objects → "field is value" patterns

### 2. Speech Synthesis (`src/speech_synthesis/`)

**`semantic_formatter.py`**
- Converts semantic elements to Speech Markdown
- Maps document structure to timing/emotion cues
- Example: `H1` → `(excited)[This is the title]`

**`emotion_detector.py`**
- Analyzes content for emotional context
- Headers → excitement, code → neutral, warnings → concern
- Integrates with TTS emotion parameters

**`speech_markdown.py`**
- Implements Speech Markdown syntax
- Converts to platform-specific SSML (Chatterbox, Azure, etc.)
- Handles timing: `[2s]`, emphasis: `**text**`, emotion: `(whisper)[text]`

## Implementation Plan

### Phase 1: Minimal Viable Pipeline
- [ ] Create base parser interface and semantic data structures
- [ ] Implement basic markdown parser (headers, bold, italic only)
- [ ] Integrate with Chatterbox TTS for immediate speech output
- [ ] Build end-to-end demo: `markdown file → spoken output`
- [ ] **Test**: Parse sample README.md and verify semantic elements extracted correctly
- [ ] **Test**: Generate actual audio file from parsed markdown and confirm pitch changes for headers
- [ ] **Test**: CLI command `python stt.py --document test.md` produces audible speech

### Phase 2: Enhanced Markdown + Emotion
- [ ] Complete markdown parsing (code blocks, lists, links, emphasis)
- [ ] Implement Speech Markdown timing/emotion syntax  
- [ ] Add content-based emotion detection (headers = excitement, code = monotone)
- [ ] Enhance TTS integration with emotion parameters
- [ ] **Test**: Parse complex markdown with code blocks, lists, links - verify all elements detected
- [ ] **Test**: Generate speech with emotion tags and confirm voice changes (excited vs monotone)
- [ ] **Test**: Time pauses between list items in generated audio

### Phase 3: Multi-Format Support
- [ ] Implement HTML and JSON parsers
- [ ] Create parser factory with auto-detection
- [ ] Add configuration system for document parsing options
- [ ] Extend CLI with document format selection
- [ ] **Test**: Parse real HTML page and JSON API response - verify content extraction
- [ ] **Test**: Auto-detect format from file extension and content sniffing
- [ ] **Test**: CLI handles multiple formats: `--document file.html`, `--document data.json`

### Phase 4: Production Features
- [ ] Generate platform-specific SSML output (Azure, Google, etc.)
- [ ] Advanced emotion mapping based on document type and context
- [ ] Integration with existing text formatting pipeline for mixed content
- [ ] Performance optimization and caching
- [ ] **Test**: SSML output validates against Azure/Google schemas
- [ ] **Test**: Mixed content (markdown + transcribed text) processes correctly
- [ ] **Test**: Large document parsing performance under 2 seconds

## Integration Points

### With Existing Systems
- **text_formatting/**: Remains unchanged, handles transcription
- **STT Pipeline**: New document mode alongside existing modes
- **Configuration**: Extend `config.json` with document parsing options

### New CLI Usage
```bash
# New document-to-speech mode
python stt.py --document README.md --output-voice
python stt.py --document data.json --format speech-markdown
python stt.py --document-server --port 8770  # HTTP API for documents
```

### API Integration
```python
from src.document_parsing import parse_document
from src.speech_synthesis import format_for_tts

# Parse any document format
semantic_content = parse_document("## Hello\nThis is **important** text.")
# Convert to TTS-ready format  
tts_markup = format_for_tts(semantic_content, emotion_level="moderate")
```

## Technical Requirements

### Dependencies
- **Document Parsing**: `markdown`, `beautifulsoup4`, `python-docx` (optional)
- **TTS Integration**: `chatterbox-tts` (MIT), `azure-cognitiveservices-speech` (optional)
- **Speech Markup**: Custom implementation based on Speech Markdown spec

### Configuration
```json
{
  "document_parsing": {
    "default_format": "auto-detect",
    "emotion_detection": true,
    "preserve_formatting": false
  },
  "speech_synthesis": {
    "voice_engine": "chatterbox",
    "emotion_level": "moderate", 
    "timing_precision": "standard",
    "ssml_output": true
  }
}
```

## Testing Strategy

### Unit Tests
- Parser accuracy for each document format
- Semantic element extraction correctness
- Speech Markdown generation validation

### Integration Tests  
- End-to-end document → speech pipeline
- Multiple format support
- Emotion detection accuracy

### Manual Testing
- Real document samples (README files, JSON APIs, HTML pages)
- Voice quality assessment
- Timing and emphasis evaluation

## Benefits

1. **Reuses Existing Architecture**: Leverages proven text formatting patterns
2. **Clean Separation**: Document parsing independent of transcription
3. **MIT Licensed**: Uses only permissive open source components
4. **Extensible**: Easy to add new document formats and TTS engines
5. **Configurable**: Flexible emotion and timing control

## Future Enhancements

- PDF document support via `PyPDF2`
- Custom voice training for technical content
- Real-time document streaming
- Multi-language document support
- Integration with documentation generation tools