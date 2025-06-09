#!/bin/bash

# GPSRAG Test Runner
# Kjører alle tester for hele prosjektet

set -e

echo "🧪 Kjører GPSRAG test suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
BACKEND_TESTS=0
FRONTEND_TESTS=0
LINT_CHECKS=0

echo "📋 Test oversikt:"
echo "  - Backend tester (pytest)"
echo "  - Frontend tester (jest)"
echo "  - Linting sjekker"
echo "  - Type checking"
echo ""

# Backend tester
echo -e "${YELLOW}🐍 Kjører backend tester...${NC}"
cd services/api-gateway

if [ -f "../../venv/bin/activate" ]; then
    source ../../venv/bin/activate
    echo "✅ Aktiverte virtual environment"
else
    echo "⚠️  Virtual environment ikke funnet, bruker system Python"
fi

# Installer test-dependencies hvis nødvendig
pip install pytest pytest-asyncio pytest-cov httpx

# Opprett test-filer hvis de ikke eksisterer
mkdir -p tests
if [ ! -f "tests/test_health.py" ]; then
    cat > tests/test_health.py << 'EOF'
"""Test health endpoints"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test basic health check"""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == "1.0.0"
EOF
fi

# Kjør backend tester
if pytest tests/ -v --cov=src --cov-report=term-missing; then
    echo -e "${GREEN}✅ Backend tester: PASSED${NC}"
    BACKEND_TESTS=1
else
    echo -e "${RED}❌ Backend tester: FAILED${NC}"
fi

cd ../..

# Frontend tester
echo -e "${YELLOW}📦 Kjører frontend tester...${NC}"
cd frontend

# Opprett test-fil hvis den ikke eksisterer
mkdir -p __tests__
if [ ! -f "__tests__/index.test.tsx" ]; then
    cat > __tests__/index.test.tsx << 'EOF'
import { render, screen } from '@testing-library/react'
import Home from '../pages/index'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: '',
      asPath: '',
    }
  },
}))

describe('Home page', () => {
  it('renders without crashing', () => {
    render(<Home />)
    expect(screen.getByText('GPSRAG')).toBeInTheDocument()
  })
})
EOF
fi

# Opprett Jest config hvis den ikke eksisterer
if [ ! -f "jest.config.js" ]; then
    cat > jest.config.js << 'EOF'
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/pages/(.*)$': '<rootDir>/pages/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
}

module.exports = createJestConfig(customJestConfig)
EOF
fi

if [ ! -f "jest.setup.js" ]; then
    echo "import '@testing-library/jest-dom'" > jest.setup.js
fi

# Installer test dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom

# Kjør frontend tester (hvis de eksisterer)
if npm test -- --passWithNoTests; then
    echo -e "${GREEN}✅ Frontend tester: PASSED${NC}"
    FRONTEND_TESTS=1
else
    echo -e "${RED}❌ Frontend tester: FAILED${NC}"
fi

cd ..

# Linting sjekker
echo -e "${YELLOW}🔍 Kjører linting sjekker...${NC}"

# Backend linting
echo "Sjekker backend kode..."
cd services/api-gateway
if [ -f "../../venv/bin/activate" ]; then
    source ../../venv/bin/activate
fi

# Kjør linting hvis verktøyene er installert
pip install black isort flake8 mypy

echo "  - Running Black (formatter)..."
if black --check .; then
    echo "    ✅ Black formatting OK"
else
    echo "    ⚠️  Black formatting issues found"
fi

echo "  - Running isort (import sorting)..."
if isort --check-only .; then
    echo "    ✅ Import sorting OK"
else
    echo "    ⚠️  Import sorting issues found"
fi

echo "  - Running flake8 (style guide)..."
if flake8 --max-line-length=88 --extend-ignore=E203,W503 .; then
    echo "    ✅ Flake8 checks OK"
    LINT_CHECKS=1
else
    echo "    ⚠️  Flake8 issues found"
fi

cd ../..

# Frontend linting
echo "Sjekker frontend kode..."
cd frontend
if npm run lint; then
    echo "  ✅ ESLint checks OK"
else
    echo "  ⚠️  ESLint issues found"
fi

cd ..

# Type checking
echo -e "${YELLOW}📝 Kjører type checking...${NC}"
cd services/api-gateway
if [ -f "../../venv/bin/activate" ]; then
    source ../../venv/bin/activate
fi

echo "  - Python type checking (mypy)..."
if mypy --ignore-missing-imports src/; then
    echo "    ✅ MyPy type checking OK"
else
    echo "    ⚠️  MyPy type issues found"
fi

cd ../..

cd frontend
echo "  - TypeScript type checking..."
if npm run type-check; then
    echo "    ✅ TypeScript type checking OK"
else
    echo "    ⚠️  TypeScript type issues found"
fi

cd ..

# Sammendrag
echo ""
echo "📊 Test sammendrag:"
echo "==================="

if [ $BACKEND_TESTS -eq 1 ]; then
    echo -e "  Backend tester:     ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Backend tester:     ${RED}❌ FAILED${NC}"
fi

if [ $FRONTEND_TESTS -eq 1 ]; then
    echo -e "  Frontend tester:    ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Frontend tester:    ${RED}❌ FAILED${NC}"
fi

if [ $LINT_CHECKS -eq 1 ]; then
    echo -e "  Linting sjekker:    ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Linting sjekker:    ${YELLOW}⚠️  WARNINGS${NC}"
fi

echo ""

# Exit med feilkode hvis noen tester feilet
if [ $BACKEND_TESTS -eq 1 ] && [ $FRONTEND_TESTS -eq 1 ]; then
    echo -e "${GREEN}🎉 Alle kjerne-tester passerte!${NC}"
    exit 0
else
    echo -e "${RED}💥 Noen tester feilet. Se detaljer ovenfor.${NC}"
    exit 1
fi 