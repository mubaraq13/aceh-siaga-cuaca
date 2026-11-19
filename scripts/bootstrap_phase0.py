#!/usr/bin/env python3
"""
Phase 0 Workspace Bootstrapper — ACEH SIAGA CUACA
Membuat seluruh struktur folder standar proyek dan memastikan dokumen Phase 0 siap.
Aman dijalankan berulang kali (idempotent, tidak menghapus file pengguna).
"""

from pathlib import Path

PROJECT_DIRS = [
    "backend/app/api",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/utils",
    "backend/tests",
    "frontend/src/app",
    "frontend/src/components",
    "frontend/src/features",
    "frontend/src/hooks",
    "frontend/src/lib",
    "frontend/src/types",
    "frontend/public",
    "data/raw/bmkg",
    "data/raw/bpba",
    "data/raw/bnpb",
    "data/processed",
    "data/external",
    "data/demo",
    "notebooks",
    "src/data_collection",
    "src/data_processing",
    "src/analytics",
    "src/geospatial",
    "src/machine_learning",
    "models/trained",
    "models/evaluation",
    "database/migrations",
    "docs",
    "scripts",
    "tests",
]

PYTHON_PACKAGES = [
    "backend/app",
    "backend/app/api",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/utils",
    "src",
    "src/data_collection",
    "src/data_processing",
    "src/analytics",
    "src/geospatial",
    "src/machine_learning",
]


def bootstrap_workspace(base_dir: Path = Path(".")) -> None:
    print(f"[PHASE 0] Menginisialisasi struktur direktori di: {base_dir.resolve()}")
    for rel_dir in PROJECT_DIRS:
        dir_path = base_dir / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep = dir_path / ".gitkeep"
        if not any(dir_path.iterdir()):
            gitkeep.touch()

    for pkg_dir in PYTHON_PACKAGES:
        init_file = base_dir / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Aceh Siaga Cuaca module."""\n', encoding="utf-8")

    print("[PHASE 0] Struktur folder selesai diverifikasi dan dibuat.")


if __name__ == "__main__":
    bootstrap_workspace()