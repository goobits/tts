# Test Fixtures for Document-to-Speech

This directory contains sample documents for testing the document-to-speech functionality.

## Available Test Documents

### 1. Technical Document (`technical_document.md`)
- **Type**: API documentation
- **Expected emotion profile**: Technical
- **Features**: Code blocks, technical terms, structured lists
- **Use case**: Testing technical content processing

### 2. Marketing Page (`marketing_page.html`)
- **Type**: Sales/marketing content
- **Expected emotion profile**: Marketing
- **Features**: Emphatic language, call-to-action, testimonials
- **Use case**: Testing marketing emotion detection and emphasis

### 3. Story Narrative (`story_narrative.md`)
- **Type**: Fiction/narrative content
- **Expected emotion profile**: Narrative
- **Features**: Dialogue, descriptive text, chapter structure
- **Use case**: Testing narrative flow and pacing

### 4. Tutorial Guide (`tutorial_guide.md`)
- **Type**: Step-by-step tutorial
- **Expected emotion profile**: Tutorial
- **Features**: Numbered steps, code examples, explanations
- **Use case**: Testing instructional content processing

### 5. Data Export (`data_export.json`)
- **Type**: Structured data report
- **Expected emotion profile**: Technical/neutral
- **Features**: Nested JSON structure, metrics, data
- **Use case**: Testing JSON-to-speech conversion

## Testing Commands

```bash
# Test technical document with auto emotion detection
tts --document tests/fixtures/technical_document.md --stream

# Test marketing HTML with SSML generation
tts --document tests/fixtures/marketing_page.html --ssml-platform azure --save

# Test narrative with custom emotion profile
tts --document tests/fixtures/story_narrative.md --emotion-profile narrative --stream

# Test tutorial with performance measurement
time tts --document tests/fixtures/tutorial_guide.md --save

# Test JSON data export
tts --document tests/fixtures/data_export.json --save
```

## Expected Behaviors

- **Technical documents**: Steady pace, clear pronunciation of technical terms
- **Marketing content**: Energetic delivery, emphasis on key selling points
- **Narrative content**: Natural flow, appropriate pauses for dramatic effect
- **Tutorial content**: Measured pace, clear step delineation
- **JSON data**: Structured presentation of hierarchical information