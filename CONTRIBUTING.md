# Contributing to Claude-Jester Desktop Extension

We welcome contributions to the Claude-Jester Desktop Extension! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/claude-jester-desktop-extension.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Run tests**: `pytest tests/`
6. **Submit a pull request**

## 🧪 Development Setup

```bash
# Clone the repository
git clone https://github.com/matthewstanton/claude-jester-desktop-extension.git
cd claude-jester-desktop-extension

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Build extension
python scripts/build.py
```

## 📝 Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Code Formatting

We use `black` and `flake8` for code formatting:

```bash
# Format code
black server/ tests/ scripts/

# Check formatting
flake8 server/ tests/ scripts/
```

## 🧪 Testing

- Write tests for all new functionality
- Ensure existing tests pass
- Aim for high test coverage
- Include both unit tests and integration tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=server --cov-report=html

# Run specific test file
pytest tests/test_basic.py -v
```

## 🛡️ Security

- All security-related changes require thorough review
- Follow secure coding practices
- Report security vulnerabilities privately to security@claude-jester.dev
- Include security tests for new features

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings to all new functions and classes
- Update CHANGELOG.md for all changes
- Include examples in documentation

## 🔄 Pull Request Process

1. **Create a descriptive title**
2. **Provide detailed description** of changes
3. **Reference any related issues**
4. **Ensure all tests pass**
5. **Update documentation** as needed
6. **Request review** from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## 🏷️ Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `security`: Security-related issue
- `documentation`: Documentation improvement
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed

## 🌟 Recognition

Contributors will be recognized in:
- README.md contributors section
- CHANGELOG.md acknowledgments
- Annual contributor highlights

## 📧 Getting Help

- **General questions**: Open a GitHub issue
- **Security issues**: security@claude-jester.dev
- **Feature requests**: GitHub discussions
- **Bug reports**: GitHub issues with bug template

Thank you for contributing to Claude-Jester! 🃏
