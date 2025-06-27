#!/bin/bash
# publish_to_pypi.sh - Automated PyPI publishing script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Ultimate AI CLI Agent - PyPI Publishing Script${NC}"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Are you in the project root?${NC}"
    exit 1
fi

# Check if required tools are installed
command -v python >/dev/null 2>&1 || { echo -e "${RED}❌ Python is required but not installed.${NC}"; exit 1; }
command -v twine >/dev/null 2>&1 || { echo -e "${YELLOW}⚠️  Installing twine...${NC}"; pip install twine; }

# Install build if not available
python -c "import build" 2>/dev/null || { echo -e "${YELLOW}⚠️  Installing build...${NC}"; pip install build; }

# Get version from pyproject.toml
VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")
echo -e "${BLUE}📦 Building version: ${VERSION}${NC}"

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/

# Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
if command -v pytest >/dev/null 2>&1; then
    python -m pytest -xvs || { echo -e "${RED}❌ Tests failed. Aborting.${NC}"; exit 1; }
else
    echo -e "${YELLOW}⚠️  pytest not found, skipping tests${NC}"
fi

# Build the package
echo -e "${YELLOW}🔨 Building package...${NC}"
python -m build --wheel --sdist

# Check the build
echo -e "${YELLOW}🔍 Checking package...${NC}"
twine check dist/*

# Ask for confirmation before publishing
echo -e "${BLUE}📋 Package Contents:${NC}"
ls -la dist/

echo ""
read -p "Do you want to publish to TestPyPI first? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧪 Publishing to TestPyPI...${NC}"
    twine upload --repository testpypi dist/* --skip-existing
    echo -e "${GREEN}✅ Published to TestPyPI successfully!${NC}"
    echo -e "${BLUE}🔗 Check it at: https://test.pypi.org/project/ultimate-ai-cli-agent/${NC}"
    echo ""
    
    read -p "Test installation looks good? Proceed to PyPI? (y/n): " -n 1 -r
    echo ""
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚀 Publishing to PyPI...${NC}"
    twine upload dist/* --skip-existing
    echo -e "${GREEN}✅ Published to PyPI successfully!${NC}"
    echo -e "${BLUE}🔗 Package available at: https://pypi.org/project/ultimate-ai-cli-agent/${NC}"
    echo ""
    echo -e "${GREEN}🎉 Users can now install with:${NC}"
    echo -e "${BLUE}   pip install ultimate-ai-cli-agent[full]${NC}"
else
    echo -e "${YELLOW}⏸️  Publishing cancelled by user${NC}"
fi

echo ""
echo -e "${GREEN}✨ Publishing process completed!${NC}"
