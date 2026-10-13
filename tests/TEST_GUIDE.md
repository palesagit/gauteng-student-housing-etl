# 🧪 Test Suite Documentation

This directory contains the automated unit tests for the Gauteng Student Housing ETL pipeline.

---

## 📋 Prerequisites

Ensure all required dependencies (including `pytest`, `pytest-cov`, and `pandas`) are installed:

```bash
pip install -r requirements.txt
```

---

## 🚀 Commands to Run Tests

### 1. Run All Tests
Execute all tests verbosely:
```bash
pytest tests/ -v
```

Or via Python standard library execution:
```bash
python -m pytest tests/ -v
```

---

### 2. Run a Specific Test File
```bash
pytest tests/test_transform.py -v
```

---

### 3. Run a Specific Test Class
```bash
pytest tests/test_transform.py::TestCurrencyCleaning -v
```

---

### 4. Run a Single Test Function
```bash
pytest tests/test_transform.py::TestCurrencyCleaning::test_clean_currency_parses_standard_rand_string -v
```

---

### 5. Run with Coverage Report
Generate a terminal report showing test coverage across the `src/` modules:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## 🗂️ Test Suite Coverage

The unit test suite in [`tests/test_transform.py`](test_transform.py) covers:

- **Currency Cleaning (`TestCurrencyCleaning`)**: Verifies parsing of raw Rand strings (e.g., `"R 4,800 / month"`, `"R3500pm"`), numbers, and `None` values.
- **NSFAS Accreditation Parsing (`TestNsfasParsing`)**: Verifies normalization of accreditation status text into Boolean flags.
- **Amenity Detection (`TestAmenityParsing`)**: Tests detection of Wi-Fi and load-shedding backup power (Generator / Solar).
- **Listing Transformation (`TestListingTransformation`)**: Validates full record transformation and conversion to Pandas DataFrame.
