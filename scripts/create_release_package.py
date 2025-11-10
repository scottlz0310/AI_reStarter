#!/usr/bin/env python3
"""
Release package creation script
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_release_package():
    """Create release package"""
    print("Creating release package...")

    # Create release directory
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()

    # Copy required files
    files_to_copy = [
        ("dist/AI_reStarter.exe", "AI_reStarter.exe"),
        ("README.md", "README.md"),
        ("kiro_config.json", "kiro_config.json"),
    ]

    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = release_dir / dst
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {src} -> {dst}")

    # Copy template directories
    template_dirs = ["amazonq_templates", "error_templates"]
    for template_dir in template_dirs:
        src_dir = Path(template_dir)
        dst_dir = release_dir / template_dir
        if src_dir.exists():
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            print(f"Copied: {template_dir}/")


def create_zip_package(version=None):
    """Create ZIP package"""
    if version is None:
        version = os.environ.get("GITHUB_REF_NAME", "v0.1.0")

    print("Creating ZIP package...")

    zip_path = Path(f"AI_reStarter-{version}.zip")
    release_dir = Path("release")

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(release_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(release_dir)
                zipf.write(file_path, arc_path)

    print(f"Created: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    create_release_package()
    create_zip_package()
