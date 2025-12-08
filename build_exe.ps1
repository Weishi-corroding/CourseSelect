#!/usr/bin/env powershell
# Packaging script: create venv, install deps, and build single-file exe with PyInstaller

$ErrorActionPreference = 'Stop'

Write-Host "[build_exe] Creating virtual environment .venv"
python -m venv .venv

Write-Host "[build_exe] Activating virtual environment and installing dependencies"
. .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

Write-Host "[build_exe] Cleaning previous build artifacts"
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }
Get-ChildItem -Path . -Filter *.spec -File -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }

Write-Host "[build_exe] Running PyInstaller to build single-file GUI exe (no console). This may take several minutes."
pyinstaller --noconfirm --onefile --windowed --icon=logo.ico --add-data "logo.ico;." main.py

Write-Host "[build_exe] Build finished. Check the dist folder for the generated exe."
Write-Host "[build_exe] Note: Selenium requires a matching browser driver (eg. msedgedriver) present on the target system or in PATH."