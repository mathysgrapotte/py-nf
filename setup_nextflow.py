#!/usr/bin/env python3
"""
Setup script for downloading and building Nextflow for py-nf.

This script automates the process of:
1. Creating a .env file with the Nextflow JAR path
2. Cloning the Nextflow repository
3. Building the Nextflow fat JAR with all dependencies
4. Verifying the setup

Usage:
    python setup_nextflow.py [--force] [--version VERSION]

Options:
    --force     Force rebuild even if JAR already exists
    --version   Specify Nextflow version to build (e.g., v25.10.0)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


class NextflowSetup:
    def __init__(self, force=False, version=None):
        self.force = force
        self.version = version
        self.project_root = Path(__file__).parent.absolute()
        self.nextflow_dir = self.project_root / "nextflow"
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"

        # Determine jar path based on version
        if version:
            version_str = version.lstrip('v')
            self.jar_path = self.nextflow_dir / "build" / "releases" / f"nextflow-{version_str}-one.jar"
            self.env_jar_path = f"nextflow/build/releases/nextflow-{version_str}-one.jar"
        else:
            # Use default from .env.example or fallback
            self.jar_path = self.nextflow_dir / "build" / "releases" / "nextflow-25.10.0-one.jar"
            self.env_jar_path = "nextflow/build/releases/nextflow-25.10.0-one.jar"

    def print_step(self, message):
        """Print a step message with formatting."""
        print(f"\n{'='*60}")
        print(f"  {message}")
        print(f"{'='*60}")

    def print_info(self, message):
        """Print an info message."""
        print(f"ℹ️  {message}")

    def print_success(self, message):
        """Print a success message."""
        print(f"✓ {message}")

    def print_error(self, message):
        """Print an error message."""
        print(f"✗ {message}", file=sys.stderr)

    def check_prerequisites(self):
        """Check if required tools are installed."""
        self.print_step("Checking prerequisites")

        required_tools = {
            'git': 'Git is required to clone the Nextflow repository',
            'make': 'Make is required to build Nextflow',
            'java': 'Java is required to build Nextflow (Java 17+)'
        }

        missing = []
        for tool, description in required_tools.items():
            if shutil.which(tool) is None:
                self.print_error(f"{tool} not found: {description}")
                missing.append(tool)
            else:
                self.print_success(f"{tool} found")

        if missing:
            self.print_error(f"\nMissing tools: {', '.join(missing)}")
            return False

        return True

    def check_existing_setup(self):
        """Check if Nextflow is already set up."""
        if not self.force and self.jar_path.exists():
            self.print_info(f"Nextflow JAR already exists at: {self.jar_path}")
            self.print_info("Use --force to rebuild")
            return True
        return False

    def create_env_file(self):
        """Create .env file from .env.example."""
        self.print_step("Creating .env file")

        if self.env_file.exists() and not self.force:
            self.print_info(".env file already exists")
            return True

        if not self.env_example.exists():
            self.print_error(f".env.example not found at {self.env_example}")
            return False

        try:
            # Read example and update path
            with open(self.env_example, 'r') as f:
                content = f.read()

            # Replace the jar path
            updated_content = f"# Nextflow configuration\n"
            updated_content += f"# Path to the Nextflow jar file (relative to project root)\n"
            updated_content += f"# Use the -one.jar file which includes all dependencies\n"
            updated_content += f"NEXTFLOW_JAR_PATH={self.env_jar_path}\n"

            with open(self.env_file, 'w') as f:
                f.write(updated_content)

            self.print_success(f"Created .env file with JAR path: {self.env_jar_path}")
            return True
        except Exception as e:
            self.print_error(f"Failed to create .env file: {e}")
            return False

    def clone_nextflow(self):
        """Clone the Nextflow repository."""
        self.print_step("Cloning Nextflow repository")

        if self.nextflow_dir.exists():
            if self.force:
                self.print_info("Nextflow directory exists, using existing clone")
            else:
                self.print_info("Nextflow directory already exists")
            return True

        try:
            self.print_info("Cloning from https://github.com/nextflow-io/nextflow.git")
            self.print_info("This may take a few minutes...")

            result = subprocess.run(
                ['git', 'clone', 'https://github.com/nextflow-io/nextflow.git', str(self.nextflow_dir)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                self.print_error(f"Git clone failed: {result.stderr}")
                return False

            self.print_success("Cloned Nextflow repository")

            # Checkout specific version if requested
            if self.version:
                self.print_info(f"Checking out version {self.version}")
                result = subprocess.run(
                    ['git', 'checkout', self.version],
                    cwd=self.nextflow_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.print_error(f"Failed to checkout version {self.version}: {result.stderr}")
                    return False
                self.print_success(f"Checked out {self.version}")

            return True
        except subprocess.TimeoutExpired:
            self.print_error("Git clone timed out after 5 minutes")
            return False
        except Exception as e:
            self.print_error(f"Failed to clone Nextflow: {e}")
            return False

    def build_nextflow(self):
        """Build Nextflow using make pack."""
        self.print_step("Building Nextflow")

        if not self.nextflow_dir.exists():
            self.print_error("Nextflow directory not found")
            return False

        try:
            self.print_info("Running 'make pack' to build Nextflow fat JAR")
            self.print_info("This will take a few minutes (first build may take longer)...")

            result = subprocess.run(
                ['make', 'pack'],
                cwd=self.nextflow_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                self.print_error(f"Build failed: {result.stderr}")
                self.print_error(f"Stdout: {result.stdout}")
                return False

            self.print_success("Built Nextflow successfully")

            # Show build output summary
            if "BUILD SUCCESSFUL" in result.stdout:
                self.print_info("Build completed successfully")

            return True
        except subprocess.TimeoutExpired:
            self.print_error("Build timed out after 10 minutes")
            return False
        except Exception as e:
            self.print_error(f"Failed to build Nextflow: {e}")
            return False

    def verify_setup(self):
        """Verify that the setup was successful."""
        self.print_step("Verifying setup")

        if not self.jar_path.exists():
            self.print_error(f"JAR file not found at: {self.jar_path}")
            return False

        jar_size = self.jar_path.stat().st_size / (1024 * 1024)  # Size in MB
        self.print_success(f"JAR file found: {self.jar_path}")
        self.print_info(f"JAR size: {jar_size:.1f} MB")

        if not self.env_file.exists():
            self.print_error(".env file not found")
            return False

        self.print_success(".env file configured")

        return True

    def run(self):
        """Run the complete setup process."""
        print("\n🚀 Nextflow Setup for py-nf\n")

        # Check prerequisites
        if not self.check_prerequisites():
            return False

        # Check if already set up
        if self.check_existing_setup():
            self.print_success("\n✓ Nextflow is already set up!")
            return True

        # Create .env file
        if not self.create_env_file():
            return False

        # Clone repository
        if not self.clone_nextflow():
            return False

        # Build Nextflow
        if not self.build_nextflow():
            return False

        # Verify setup
        if not self.verify_setup():
            return False

        # Success!
        print("\n" + "="*60)
        print("  ✓ Setup completed successfully!")
        print("="*60)
        print("\nYou can now run:")
        print("  uv run python tests/test_integration.py")
        print("\nOr use the API:")
        print("  from pynf import run_module")
        print('  result = run_module("nextflow_scripts/hello-world.nf")')
        print()

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Set up Nextflow for py-nf',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild even if JAR already exists'
    )
    parser.add_argument(
        '--version',
        type=str,
        help='Specify Nextflow version to build (e.g., v25.10.0)'
    )

    args = parser.parse_args()

    setup = NextflowSetup(force=args.force, version=args.version)
    success = setup.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
