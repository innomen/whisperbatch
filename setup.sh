#!/usr/bin/env bash
set -e

echo "🌀 Whisper Batch Installer (Garuda/Arch version)"

OS="$(uname -s)"

# Check for tkinter and offer install
if [[ "$OS" == "Linux" ]]; then
  echo "🔎 Checking for tkinter support..."

  if python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "✅ Tkinter found."
  else
    echo "🚩 Tkinter missing."

    if command -v pacman >/dev/null 2>&1; then
      echo "👉 Installing Tkinter via pacman ('tk' package)..."
      sudo pacman -Sy --needed tk
      echo "⚠️ If your python is from pyenv or was compiled before installing 'tk',"
      echo "   you need to rebuild it after 'tk' is present to get tkinter support:"
      echo "Example:"
      echo "   pyenv uninstall 3.11.6"
      echo "   sudo pacman -S tk"
      echo "   pyenv install 3.11.6"
    else
      echo "⚠️ pacman not found. Please install tkinter for your distro manually."
    fi
  fi
else
  echo "⚠️ Non-Linux system detected. Please manually ensure tkinter support."
fi

echo "🐍 Creating virtual environment..."
VENV="./venv_whisper"

if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

echo "🐍 Upgrading pip in venv..."
"$VENV/bin/python" -m pip install --upgrade pip

echo "📦 Installing whisper and ffmpeg-python..."
"$VENV/bin/pip" install git+https://github.com/openai/whisper.git ffmpeg-python

# Check for ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "⚠️ ffmpeg NOT found. Installing via pacman..."
  if command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --needed ffmpeg
  else
    echo "⚠️ pacman not found. Please install ffmpeg manually."
  fi
else
  echo "🎬 Found ffmpeg: $(command -v ffmpeg)"
fi

echo "⬇️ Downloading large-v3 whisper model (~3GB, one-time)..."
"$VENV/bin/python" -c "import whisper; whisper.load_model('large-v3')"

echo
echo "✅ Setup done!"
echo
echo "👉 Activate your virtual environment:"
echo "  Bash/zsh: "
echo "     source $VENV/bin/activate"
echo "  Fish shell:"
echo "     source $VENV/bin/activate.fish"
echo
echo "Run:"
echo "     python WhisperBatch.py"
echo
