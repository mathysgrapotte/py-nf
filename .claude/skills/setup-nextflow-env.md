# setup-nextflow-env

## Description

Automate Nextflow JAR setup and validate the py-nf development environment. This skill guides users through cloning Nextflow, building the fat JAR, configuring environment variables, and verifying the installation works correctly.

## When to Use

Use this skill when:

- **Initial setup** of py-nf development environment
- **JAR not found** error when running py-nf
- **Environment broken** after system changes
- **Upgrading** Nextflow version
- **Onboarding** new developers to the project
- **Fixing** JVM startup or classpath issues

## Keywords

setup, environment, nextflow jar, installation, configuration, troubleshooting, onboarding

## Instructions

When the user needs to set up or fix their environment, follow these steps:

### 1. Assess Current State

Check what's already set up:

```bash
# Check for .env file
cat .env 2>/dev/null || echo "No .env file found"

# Check if JAR exists
if [ -f "$NEXTFLOW_JAR_PATH" ]; then
    echo "JAR exists at: $NEXTFLOW_JAR_PATH"
else
    echo "JAR not found"
fi

# Check if Nextflow repo exists
ls -d nextflow 2>/dev/null || echo "Nextflow repo not cloned"

# Check Python environment
uv run python -c "import pynf" 2>/dev/null && echo "✓ pynf importable" || echo "✗ pynf not installed"
```

### 2. Run Automated Setup

The project includes `setup_nextflow.py` which automates the setup:

```bash
# Basic setup (uses default version)
python setup_nextflow.py

# Options:
python setup_nextflow.py --force              # Rebuild JAR even if exists
python setup_nextflow.py --version v25.10.0   # Specific Nextflow version
python setup_nextflow.py --help               # Show all options
```

**What the script does:**

1. Clones Nextflow from GitHub (if not exists)
2. Checks out specified version
3. Builds fat JAR using `make pack`
4. Creates/updates `.env` with JAR path
5. Verifies the setup works

### 3. Manual Setup (if automated fails)

If `setup_nextflow.py` fails, follow manual steps:

#### Step 3.1: Clone Nextflow

```bash
# Clone from GitHub
git clone https://github.com/nextflow-io/nextflow.git

# Navigate to repo
cd nextflow

# Checkout specific version (optional)
git checkout v25.10.0
```

#### Step 3.2: Build Fat JAR

```bash
# Build using Makefile
make pack

# This creates: build/releases/nextflow-<version>-one.jar
# Wait for build to complete (can take 5-10 minutes)
```

**Build requirements:**

- Java 11 or later (for building)
- Groovy (included in build)
- Internet connection (downloads dependencies)

**Common build issues:**

**Build fails with "Java version" error:**

```bash
# Check Java version
java -version
# Need Java 11+, install if needed:
# macOS: brew install openjdk@11
# Linux: apt-get install openjdk-11-jdk
```

**Build fails with memory error:**

```bash
# Increase Gradle memory
export GRADLE_OPTS="-Xmx4g"
make pack
```

**Build fails with dependency download errors:**

```bash
# Clean and retry
make clean
make pack
```

#### Step 3.3: Configure Environment

Create `.env` file in project root:

```bash
# From py-nf directory
cat > .env << 'EOF'
NEXTFLOW_JAR_PATH=/absolute/path/to/nextflow/build/releases/nextflow-25.10.0-one.jar
EOF
```

**Find JAR path:**

```bash
# From nextflow directory
ls -la build/releases/*.jar

# Get absolute path
realpath build/releases/nextflow-*-one.jar
```

#### Step 3.4: Install py-nf Package

```bash
# Install in editable mode
uv pip install -e .

# Verify installation
uv run python -c "import pynf; print('✓ pynf installed')"
```

### 4. Verify Setup

Run verification tests:

```bash
# Test 1: Import check
uv run python -c "from pynf import NextflowEngine; print('✓ Import successful')"

# Test 2: JVM startup check
uv run python << 'EOF'
from pynf import NextflowEngine
engine = NextflowEngine()
print("✓ JVM started successfully")
EOF

# Test 3: Run basic test
uv run pytest tests/test_integration.py::test_basic_engine -v

# Test 4: Run full integration tests
uv run pytest tests/test_integration.py -v
```

### 5. Troubleshoot Common Issues

#### Issue 1: JAR Not Found

**Error:**

```
FileNotFoundError: Nextflow JAR not found at: nextflow/build/releases/...
```

**Solutions:**

```bash
# Verify JAR exists
ls -la nextflow/build/releases/

# Rebuild if missing
cd nextflow && make pack

# Update .env with correct path
echo "NEXTFLOW_JAR_PATH=$(realpath nextflow/build/releases/nextflow-*-one.jar)" > .env
```

#### Issue 2: JVM Start Failure

**Error:**

```
java.lang.UnsatisfiedLinkError: ... jpype._jvmfinder
```

**Solutions:**

```bash
# Reinstall JPype
uv pip uninstall jpype1
uv pip install jpype1

# Check Java installation
java -version

# Set JAVA_HOME if needed
export JAVA_HOME=$(/usr/libexec/java_home)  # macOS
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))  # Linux
```

#### Issue 3: Import Errors

**Error:**

```
ModuleNotFoundError: No module named 'pynf'
```

**Solutions:**

```bash
# Ensure in virtual environment
source .venv/bin/activate

# Reinstall in editable mode
uv pip install -e .

# Verify project structure
ls -la src/pynf/
```

#### Issue 4: Native Access Warnings

**Warning:**

```
WARNING: Illegal reflective access by jpype...
```

**Solution:**

```bash
# Suppress with environment variable
export JAVA_TOOL_OPTIONS="--enable-native-access=ALL-UNNAMED"

# Add to .env file
echo "JAVA_TOOL_OPTIONS=--enable-native-access=ALL-UNNAMED" >> .env
```

#### Issue 5: Old Nextflow Version

**Issue:** Using Nextflow < 23.10 (missing TraceObserverV2)

**Solution:**

```bash
cd nextflow
git fetch --tags
git checkout v25.10.0  # Or later version
make clean
make pack
# Update .env with new JAR path
```

### 6. Environment Configuration Reference

Complete `.env` file template:

```bash
# Required: Path to Nextflow fat JAR
NEXTFLOW_JAR_PATH=/absolute/path/to/nextflow/build/releases/nextflow-25.10.0-one.jar

# Optional: Suppress JVM warnings
JAVA_TOOL_OPTIONS=--enable-native-access=ALL-UNNAMED

# Optional: Set Java home explicitly
JAVA_HOME=/path/to/java/home

# Optional: Increase JVM memory for large workflows
NXF_OPTS=-Xmx8g

# Optional: Nextflow work directory
NXF_WORK=/tmp/nextflow-work
```

### 7. Version Management

**Check current version:**

```bash
# From JAR filename
ls nextflow/build/releases/*.jar | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'

# From Nextflow git repo
cd nextflow && git describe --tags
```

**Upgrade to new version:**

```bash
cd nextflow
git fetch --tags
git checkout v25.12.0  # New version
make clean
make pack

# Update .env
echo "NEXTFLOW_JAR_PATH=$(realpath build/releases/nextflow-*-one.jar)" > ../.env

# Test new version
cd ..
uv run pytest tests/test_integration.py -v
```

**Multiple versions:**

```bash
# Build different versions in separate directories
git clone https://github.com/nextflow-io/nextflow.git nextflow-25.10
git clone https://github.com/nextflow-io/nextflow.git nextflow-25.12

# Switch by updating .env
echo "NEXTFLOW_JAR_PATH=$(realpath nextflow-25.10/build/releases/*.jar)" > .env
```

### 8. Fresh Install Checklist

For completely new setup, verify each step:

- [ ] Python 3.8+ installed
- [ ] uv package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Java 11+ installed (`java -version`)
- [ ] Nextflow repo cloned
- [ ] Nextflow JAR built (`make pack` completed)
- [ ] `.env` file created with correct JAR path
- [ ] py-nf installed in editable mode (`uv pip install -e .`)
- [ ] Virtual environment active (`source .venv/bin/activate`)
- [ ] Imports work (`python -c "import pynf"`)
- [ ] Basic test passes (`pytest tests/test_integration.py::test_basic_engine`)

### 9. Development Environment Tips

**Recommended aliases:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias pynf-test='uv run pytest tests/test_integration.py -v'
alias pynf-env='source .venv/bin/activate'
alias pynf-rebuild='cd nextflow && make pack && cd ..'
```

**IDE setup (VS Code):**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.envFile": "${workspaceFolder}/.env",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

**Pre-commit hook:**

```bash
# .git/hooks/pre-commit
#!/bin/bash
uv run pytest tests/test_integration.py -v || exit 1
```

## Quick Start (TL;DR)

For users who want fastest path to working environment:

```bash
# 1. Clone and setup
git clone <py-nf-repo>
cd py-nf

# 2. Automated setup
python setup_nextflow.py

# 3. Verify
uv run pytest tests/test_integration.py -v

# Done!
```

## Integration with Development Workflow

**When to run this skill:**

- New developer setup (Day 1)
- After OS update or Java upgrade
- When switching branches with version changes
- CI/CD environment setup
- Container image builds

**After setup, use:**

- `test-nextflow-module` to validate environment works
- `create-integration-test` to add test coverage
- Regular development workflow

## Related Skills

- **test-nextflow-module**: Verify setup works by running test script
- **debug-observer-events**: Troubleshoot if tests fail after setup
- **analyze-java-types**: Inspect Nextflow classes after JVM starts
