# Running Tests

The linux-tweaker project uses pytest for testing.

## Setup

Since the system uses an externally-managed Python environment, you need to create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_preset_manager.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Coverage

Current test files:
- `test_preset_manager.py` - Tests for PresetManager (JSON loading, search, error handling)
- `test_de_detector.py` - Tests for DEDetector (environment detection, process detection, config detection)
- `test_theme_engine.py` - Tests for ThemeEngine base class (URL validation, archive extraction, change calculation)
