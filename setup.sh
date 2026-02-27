#!/bin/bash
# YT Automation - Setup Script
# Sets up the full development environment

set -e

echo "============================================"
echo "  YT Automation - Setup"
echo "  AI-Powered YouTube Shorts Creator"
echo "============================================"
echo ""

# ── 1. Check Node.js ────────────────────────────────────────────────
echo "[1/6] Checking Node.js..."
if command -v node &> /dev/null; then
    echo "  ✓ Node.js $(node --version)"
else
    echo "  ✗ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# ── 2. Check Python ─────────────────────────────────────────────────
echo "[2/6] Checking Python..."
if command -v python3 &> /dev/null; then
    echo "  ✓ Python $(python3 --version)"
else
    echo "  ✗ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# ── 3. Check FFmpeg ──────────────────────────────────────────────────
echo "[3/6] Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "  ✓ FFmpeg available"
else
    echo "  ✗ FFmpeg not found. Install with: sudo apt install ffmpeg"
    echo "    (continuing setup, but video processing will not work)"
fi

# ── 4. Install Node dependencies ────────────────────────────────────
echo "[4/6] Installing Node.js dependencies..."
npm install

# ── 5. Set up Python virtual environment and dependencies ────────────
echo "[5/6] Setting up Python backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# ── 6. Check Ollama (optional) ──────────────────────────────────────
echo "[6/6] Checking Ollama (local LLM)..."
if command -v ollama &> /dev/null; then
    echo "  ✓ Ollama available"
    echo "  Pulling llama3.2 model (this may take a while)..."
    ollama pull llama3.2 || echo "  ⚠ Could not pull model. Run manually: ollama pull llama3.2"
else
    echo "  ✗ Ollama not found (optional - install from https://ollama.com)"
    echo "    Without Ollama, the app falls back to rule-based analysis"
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "To start the app:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    python run.py"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    npm run dev"
echo ""
echo "  Then open http://localhost:3000"
echo ""
echo "ML Pipeline Components:"
echo "  - Whisper: Audio transcription (auto-downloads on first use)"
echo "  - CLIP: Visual analysis (auto-downloads on first use)"
echo "  - Ollama: Local LLM (requires separate install)"
echo "  - librosa: Audio energy analysis"
echo "  - PySceneDetect: Scene detection"
echo "  - FFmpeg: Video processing"
echo ""
