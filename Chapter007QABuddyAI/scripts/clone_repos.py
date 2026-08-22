"""
QABuddy.ai — Clone Repos Script
Clones the Selenium and Playwright framework repos into the data directories.
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import settings


def clone_repo(url: str, target_dir: Path) -> bool:
    """Clone a git repository into the target directory."""
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"⚠️  {target_dir.name} already has content. Skipping clone.")
        print(f"   To re-clone, delete {target_dir} first.")
        return True

    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 Cloning {url}...")
    print(f"   → {target_dir}")

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print(f"✅ Successfully cloned {url}")
            return True
        else:
            print(f"❌ Clone failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Git is not installed. Please install Git first.")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Clone timed out after 5 minutes.")
        return False


def main():
    print("=" * 60)
    print("QABuddy.ai — Repository Cloner")
    print("=" * 60)

    repos = [
        (settings.selenium_repo_url, settings.get_data_path("selenium_repo")),
        (settings.playwright_repo_url, settings.get_data_path("playwright_repo")),
    ]

    success_count = 0
    for url, target in repos:
        if clone_repo(url, target):
            success_count += 1
        print()

    print(f"\n{'=' * 60}")
    print(f"Done: {success_count}/{len(repos)} repos cloned successfully")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
