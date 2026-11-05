#!/usr/bin/env bash
# Render Build Script for GQT HRMS Backend
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing backend dependencies..."
pip install -r backend/requirements.txt

echo "==> Collecting static assets via WhiteNoise..."
python backend/manage.py collectstatic --no-input --settings=config.settings.production

echo "==> Applying database migrations on Supabase..."
python backend/manage.py migrate --settings=config.settings.production

echo "==> Build completed successfully!"

