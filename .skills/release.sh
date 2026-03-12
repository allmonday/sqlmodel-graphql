#!/bin/bash
# Release version skill - Shell implementation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if version is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: ./release.sh <version>${NC}"
    echo "Example: ./release.sh 0.8.2"
    exit 1
fi

VERSION=$1
TAG="v$VERSION"

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}❌ Invalid version format: $VERSION${NC}"
    echo "   Version must follow SemVer (e.g., 0.8.2, 1.0.0)"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "${BLUE}📦 Release Version: ${TAG}${NC}"
echo "============================================================"
echo ""

# Check working directory
echo "🔍 Checking working directory..."
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Working directory is not clean${NC}"
    echo "   Please commit or stash your changes first"
    git status --short
    exit 1
fi
echo -e "${GREEN}✅ Working directory is clean${NC}"
echo ""

# Update version in pyproject.toml
echo "📝 Updating version to $VERSION..."
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml not found${NC}"
    exit 1
fi

sed -i.bak "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
rm -f pyproject.toml.bak
echo -e "${GREEN}✅ Updated pyproject.toml to version $VERSION${NC}"
echo ""

# Run tests
echo "🧪 Running tests..."
if ! uv run pytest; then
    echo -e "${RED}❌ Tests failed${NC}"
    git checkout pyproject.toml
    exit 1
fi
echo -e "${GREEN}✅ All tests passed${NC}"
echo ""

# Create commit
echo "📝 Creating commit..."
git add pyproject.toml uv.lock
git commit -m "bump ver"
COMMIT=$(git rev-parse --short HEAD)
echo -e "${GREEN}✅ Created commit: $COMMIT${NC}"
echo ""

# Create tag
echo "🏷️  Creating tag..."
if git tag $TAG 2>&1 | grep -q "already exists"; then
    echo -e "${RED}❌ Tag $TAG already exists${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Created tag: $TAG${NC}"
echo ""

# Push tag
echo "🚀 Pushing tag $TAG to origin..."
if ! git push origin $TAG; then
    echo -e "${RED}❌ Failed to push tag${NC}"
    echo ""
    echo "💡 Tips:"
    echo "   - Check your network connection"
    echo "   - Verify you have push permissions"
    echo "   - Try: git push origin $TAG"
    exit 1
fi
echo -e "${GREEN}✅ Tag $TAG pushed to origin${NC}"
echo ""

# Show summary
echo "============================================================"
echo -e "${GREEN}✅ Release completed successfully!${NC}"
echo "============================================================"
echo ""
echo "📦 Version: $TAG"
echo "📝 Commit: $COMMIT"
echo "🏷️  Tag: $TAG"
echo "🚀 Pushed to: origin/$TAG"
echo ""
echo "📋 Recent commits included in this release:"
git log --oneline -3 | sed 's/^/   /'
echo ""
echo -e "${GREEN}🎉 Done!${NC}"
