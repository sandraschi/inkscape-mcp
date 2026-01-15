# Inkscape MCP Zed Extension Build Script (PowerShell)
# Run this script to build the Rust extension for Zed IDE

# 1. Ensure the Wasm target exists
rustup target add wasm32-wasip1

# 2. Build the extension in release mode for Zed
Write-Host "Building Inkscape MCP Extension..." -ForegroundColor Green
cargo build --release --target wasm32-wasip1

# 3. Check if build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "---------------------------------------" -ForegroundColor Green
    Write-Host "✅ Build Successful!" -ForegroundColor Green
    Write-Host "Next: In Zed, run 'Extensions: Install Dev Extension'" -ForegroundColor Cyan
    Write-Host "and select: $PWD" -ForegroundColor Cyan
    Write-Host "---------------------------------------" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed. Check the Rust errors above." -ForegroundColor Red
}