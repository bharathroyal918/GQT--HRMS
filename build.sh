#!/usr/bin/env bash
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing backend dependencies..."
pip install -r backend/requirements.txt

echo "==> Collecting static assets via WhiteNoise..."
python backend/manage.py collectstatic --no-input --settings=config.settings.production

echo "==> Build completed successfully!"
