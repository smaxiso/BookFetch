#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Starting local verification..."

# 1. Type Checking (Mypy)
echo -e "\n${GREEN}[1/3] Running Type Checks (mypy for Python 3.9)...${NC}"
# Use --python-version 3.9 to strictly enforce 3.9 compatibility
if mypy src/ tests/ --python-version 3.9; then
    echo -e "${GREEN}✓ Type checks passed${NC}"
else
    echo -e "${RED}✗ Type checks failed${NC}"
    exit 1
fi

# 2. Linting & Formatting (Ruff)
echo -e "\n${GREEN}[2/3] Running Linters & Formatters (ruff)...${NC}"
if ruff check src/ tests/ && ruff format --check src/ tests/; then
    echo -e "${GREEN}✓ Linting & Formatting passed${NC}"
else
    echo -e "${RED}✗ Linting or Formatting failed${NC}"
    exit 1
fi

# 3. Unit Tests
echo -e "\n${GREEN}[3/3] Running Unit Tests (pytest)...${NC}"
if pytest tests/unit/; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}✨ All checks passed! You are ready to push.${NC}"
