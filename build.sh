#!/bin/bash

# Inkscape MCP Zed Extension Build Script

# 1. Ensure the Wasm target exists
rustup target add wasm32-wasip1

# 2. Build the extension in release mode for Zed
echo "Building Inkscape MCP Extension..."
cargo build --release --target wasm32-wasip1

# 3. Check if build was successful
if [ $? -eq 0 ]; then
    echo "---------------------------------------"
    echo "✅ Build Successful!"
    echo "Next: In Zed, run 'Extensions: Install Dev Extension'"
    echo "and select: $(pwd)"
    echo "---------------------------------------"
else
    echo "❌ Build failed. Check the Rust errors above."
fi