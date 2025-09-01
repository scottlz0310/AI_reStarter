#!/usr/bin/env python3
"""
Release trigger helper script
"""
import subprocess
import sys
import time


def trigger_release(version):
    """Release trigger with retry logic"""
    print(f"Triggering release for version {version}")

    # Delete existing tag
    try:
        subprocess.run(f"git tag -d {version}", shell=True, check=False)
        subprocess.run(f"git push origin :refs/tags/{version}", shell=True, check=False)
        print(f"Deleted existing tag {version}")
        time.sleep(2)  # Wait for deletion to propagate
    except Exception as e:
        print(f"Tag deletion failed (may not exist): {e}")

    # Create and push new tag
    try:
        subprocess.run(
            f'git tag -a {version} -m "Release {version}"', shell=True, check=True
        )
        print(f"Created tag {version}")

        # Try multiple push methods
        push_commands = [
            f"git push origin {version}",
            f"git push --force origin {version}",
            f"git push origin refs/tags/{version}:refs/tags/{version}",
        ]

        for cmd in push_commands:
            try:
                result = subprocess.run(
                    cmd, shell=True, check=True, capture_output=True, text=True
                )
                print(f"Successfully pushed tag with: {cmd}")
                print(f"Output: {result.stderr}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed with {cmd}: {e}")
                continue

        print("All push methods failed")
        return False

    except Exception as e:
        print(f"Tag creation failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trigger_release.py <version>")
        print("Example: python trigger_release.py v0.2.0")
        sys.exit(1)

    version = sys.argv[1]
    if not version.startswith("v"):
        version = f"v{version}"

    success = trigger_release(version)
    sys.exit(0 if success else 1)
