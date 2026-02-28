# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for TOA Generator desktop app."""

import os
import importlib

# Locate customtkinter assets for bundling
ctk_path = os.path.dirname(importlib.import_module("customtkinter").__file__)

a = Analysis(
    ["run_gui.py"],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_path, "customtkinter"),
    ],
    hiddenimports=[
        "customtkinter",
        # AI provider SDKs
        "anthropic",
        "openai",
        "google.genai",
        "google.genai.types",
        "mistralai",
        "cohere",
        # Core dependencies
        "httpx",
        "httpcore",
        "pydantic_settings",
        "pydantic",
        "docx",
        "pdfplumber",
        "pdfminer",
        "pdfminer.high_level",
        "PIL",
        "lxml",
        "lxml.etree",
        "jiter",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "fastapi",
        "uvicorn",
        "jinja2",
        "starlette",
        "multipart",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TOAGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
