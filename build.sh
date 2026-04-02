#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

# Install backend dependencies
cd backend
pip install .

# Build frontend
cd ../frontend
npm install
npx vite build
