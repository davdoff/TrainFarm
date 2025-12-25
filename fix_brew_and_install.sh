#!/bin/bash
# Script to fix Homebrew permissions and install Tesseract

echo "Fixing Homebrew permissions..."
sudo chown -R $(whoami) /usr/local/Cellar /usr/local/share /usr/local/var/homebrew /usr/local/lib /usr/local/bin

echo "Cleaning up Homebrew..."
brew cleanup

echo "Installing Tesseract and language data..."
brew install tesseract tesseract-lang --overwrite

echo "Done! Tesseract should now be installed."
tesseract --version
