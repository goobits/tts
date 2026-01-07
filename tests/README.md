# Tests

Test organization and how to run the suite.

## Structure

```
tests/
├── unit/
├── integration/
├── e2e/
├── providers/
├── fixtures/
└── mocking/
```

## Run

```bash
./scripts/test.sh
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```
