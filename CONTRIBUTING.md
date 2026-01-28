# Contributing to IBKRBot

Thank you for your interest in contributing to IBKRBot! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Interactive Brokers TWS or IB Gateway (for testing with real connections)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/IBKRBot.git
   cd IBKRBot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run smoke tests**
   ```bash
   python -m ibkrbot.smoke_test
   ```

5. **Run unit tests**
   ```bash
   pytest
   ```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/JrCheesey/IBKRBot/issues)
2. If not, create a new issue using the Bug Report template
3. Include:
   - IBKRBot version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable

### Suggesting Features

1. Check existing [Issues](https://github.com/JrCheesey/IBKRBot/issues) for similar suggestions
2. Create a new issue using the Feature Request template
3. Describe the feature and its use case

### Submitting Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run smoke test
   python -m ibkrbot.smoke_test

   # Run unit tests
   pytest

   # Test the GUI manually
   python -m ibkrbot.main
   ```

4. **Commit your changes**
   ```bash
   git commit -m "Brief description of changes"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub.

## Code Style

- Follow PEP 8 guidelines
- Use type hints where practical
- Keep functions focused and small
- Use descriptive variable names
- Add docstrings to public functions and classes

### Example

```python
def calculate_position_size(
    account_value: float,
    risk_percent: float,
    entry_price: float,
    stop_price: float
) -> int:
    """
    Calculate position size based on account risk.

    Args:
        account_value: Total account value in dollars
        risk_percent: Percentage of account to risk (e.g., 1.0 for 1%)
        entry_price: Planned entry price
        stop_price: Stop loss price

    Returns:
        Number of shares to trade
    """
    risk_amount = account_value * (risk_percent / 100)
    risk_per_share = abs(entry_price - stop_price)

    if risk_per_share == 0:
        return 0

    return int(risk_amount / risk_per_share)
```

## Project Structure

```
IBKRBot/
├── ibkrbot/
│   ├── core/           # Core business logic
│   │   ├── ibkr/       # IBKR API client, contracts, orders
│   │   ├── features/   # Trading features (proposer, placer, etc.)
│   │   └── visual/     # Chart generation
│   ├── ui/             # PySide6 GUI components
│   │   └── widgets/    # Reusable UI widgets
│   └── resources/      # Icons, sounds, etc.
├── tests/              # Unit tests
└── docs/               # Documentation
```

## Testing Guidelines

- Write tests for new functionality
- Use pytest fixtures for common setup
- Mock external dependencies (IBKR API, network calls)
- Test edge cases and error conditions

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ibkrbot

# Run specific test file
pytest tests/test_trade_journal.py

# Run tests matching a pattern
pytest -k "test_backup"
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Update CHANGELOG.md for notable changes
- Ensure all tests pass
- Respond to review feedback promptly

## Questions?

Feel free to open a Discussion on GitHub if you have questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
