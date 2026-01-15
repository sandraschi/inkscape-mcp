# PyPI Publishing Guide

**Publishing Inkscape MCP to PyPI with uv**

## 🎯 Prerequisites

### PyPI Account Setup
1. Create account at https://pypi.org/account/register/
2. Verify email address
3. Set up 2FA (recommended)
4. Create API token at https://pypi.org/manage/account/token/

### Local Setup
```bash
# Install publishing tools
uv pip install build twine

# Configure API token
# Create ~/.pypirc or use environment variables
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-AgEIcHlwaS5vcmcC..."

# Or create ~/.pypirc
# [pypi]
# username = __token__
# password = pypi-AgEIcHlwaS5vcmcC...
```

## 🏗️ Build Package

### Clean Build
```bash
# Ensure clean state
git status  # Should be clean

# Build with uv (recommended)
uv build

# Or with build tool
python -m build

# Verify build artifacts
ls dist/
# Should see: inkscape_mcp-1.2.0.tar.gz and inkscape_mcp-1.2.0-py3-none-any.whl
```

### Test Build Locally
```bash
# Install from local build
uv pip install dist/inkscape_mcp-1.2.0.tar.gz --force-reinstall

# Test installation
inkscape-mcp --help

# Run tests
uv run pytest
```

## 📦 Publish to PyPI

### Test PyPI First (Recommended)
```bash
# Upload to test PyPI
uv run twine upload --repository testpypi dist/*

# Test install from test PyPI
uv pip install --index-url https://test.pypi.org/simple/ inkscape-mcp

# Verify functionality
inkscape-mcp --version
```

### Production PyPI Upload
```bash
# Upload to production PyPI
uv run twine upload dist/*

# Verify on PyPI
# Visit: https://pypi.org/project/inkscape-mcp/
```

## 🏷️ Version Management

### Semantic Versioning
- **MAJOR.MINOR.PATCH** (e.g., 1.2.0)
- **Pre-releases**: 1.2.0a1, 1.2.0b1, 1.2.0rc1
- **Dev releases**: 1.2.0.dev1

### Update Version
```toml
# In pyproject.toml
[project]
version = "1.2.0"

# For beta releases
version = "1.2.0b1"
```

## 📋 Pre-Publish Checklist

### Code Quality
- [ ] All tests pass: `uv run pytest`
- [ ] Code formatted: `uv run ruff format`
- [ ] Linting clean: `uv run ruff check`
- [ ] Type checking: `uv run mypy`
- [ ] Security audit: `uv run bandit`

### Documentation
- [ ] README.md updated with latest features
- [ ] INSTALL.md comprehensive and tested
- [ ] CHANGELOG.md updated
- [ ] API documentation current

### Package Metadata
- [ ] Version correct in pyproject.toml
- [ ] Description accurate and compelling
- [ ] License specified (MIT)
- [ ] Authors and maintainers listed
- [ ] Keywords relevant for discovery
- [ ] Classifiers appropriate

### Distribution Files
- [ ] Source distribution built
- [ ] Wheel built
- [ ] Both files present in dist/
- [ ] File sizes reasonable (< 10MB)

### Testing
- [ ] Install from local build works
- [ ] Import test passes
- [ ] CLI commands functional
- [ ] Basic MCP operations work
- [ ] Test PyPI upload successful

## 🔄 Post-Publish Tasks

### Verify Publication
```bash
# Check PyPI page
curl https://pypi.org/pypi/inkscape-mcp/json

# Install from PyPI
pip install inkscape-mcp --upgrade

# Test installation
inkscape-mcp --version
```

### Update Documentation
- [ ] Update version badges in README
- [ ] Update installation instructions if needed
- [ ] Announce release on GitHub
- [ ] Update CHANGELOG.md with release notes

### Community Communication
- [ ] Create GitHub release with changelog
- [ ] Announce in relevant Discord servers
- [ ] Update any external documentation
- [ ] Notify MCP community channels

## 🐛 Rollback Procedures

### If Something Goes Wrong
```bash
# Delete from PyPI (within 72 hours)
# Contact PyPI admins: https://pypi.org/help/

# Or yank the release (marks as broken but keeps for dependencies)
uv run twine upload --skip-existing dist/inkscape_mcp-1.2.0.tar.gz --disable-progress-bar
```

### Emergency Fixes
1. Increment patch version (1.2.0 → 1.2.1)
2. Fix the issue
3. Rebuild and republish
4. Update dependents

## 📊 Monitoring

### Post-Publish Metrics
- **Downloads**: Check PyPI stats
- **GitHub**: Watch for issues and PRs
- **Community**: Monitor Discord/Reddit feedback
- **CI/CD**: Ensure automated tests pass

### Maintenance
- **Security**: Monitor for vulnerabilities
- **Dependencies**: Keep dependencies updated
- **Compatibility**: Test with new Python/Inkscape versions
- **Feedback**: Incorporate user feedback in updates

## 🎯 Distribution Strategy

### Target Audience
- **AI Developers**: Claude Desktop, Windsurf users
- **Graphic Designers**: Vector art professionals
- **Content Creators**: SVG workflow automation
- **Developers**: MCP server implementers

### Marketing Channels
- **GitHub**: Repository stars and forks
- **PyPI**: Package discovery and downloads
- **MCP Community**: Discord and forums
- **AI Communities**: Reddit r/ClaudeAI, r/LocalLLaMA
- **Design Communities**: Inkscape forums, graphic design subreddits

---

**Publishing Status**: Ready for PyPI publication
**Version**: 1.2.0
**PyPI Account**: sandraschi (created)
**Build System**: uv + hatchling
**Distribution**: Source + wheel