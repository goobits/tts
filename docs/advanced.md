# Advanced Usage

Pipelines, document processing, and SSML.

## Pipelines

```bash
echo "Hello" | voice
ears recording.wav | voice
echo "Hello" | brain "translate to Spanish" | voice @google
```

## Documents

```bash
voice document report.html --save
voice document README.md --emotion-profile technical
voice document data.json --save
```

## SSML

```bash
voice document content.html --ssml-platform azure --save-ssml content.ssml
voice @google --ssml content.ssml
```
