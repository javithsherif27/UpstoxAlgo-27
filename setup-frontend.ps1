# Node.js Installation and Frontend Setup Script
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Node.js Installation & Frontend Setup" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Check if Node.js is installed
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
        
        $npmVersion = npm --version 2>$null
        Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
        
        # Change to frontend directory
        Set-Location "frontend"
        
        if (Test-Path "package.json") {
            Write-Host "" 
            Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
            npm install
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "✅ Frontend dependencies installed successfully!" -ForegroundColor Green
                Write-Host ""
                Write-Host "You can now run:" -ForegroundColor Cyan
                Write-Host "  npm run dev     (development server)" -ForegroundColor White
                Write-Host "  npm run build   (production build)" -ForegroundColor White
            } else {
                Write-Host "❌ npm install failed. Try: npm install --legacy-peer-deps" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ package.json not found in frontend directory" -ForegroundColor Red
        }
        
    }
} catch {
    Write-Host "❌ Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "INSTALLATION OPTIONS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OPTION 1: Install via winget (run as administrator):" -ForegroundColor Cyan
    Write-Host "  winget install OpenJS.NodeJS" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTION 2: Manual installation:" -ForegroundColor Cyan
    Write-Host "  1. Go to: https://nodejs.org/" -ForegroundColor White
    Write-Host "  2. Download LTS version" -ForegroundColor White
    Write-Host "  3. Run installer" -ForegroundColor White
    Write-Host "  4. Restart terminal and run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTION 3: Install via Chocolatey:" -ForegroundColor Cyan
    Write-Host "  choco install nodejs" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, restart your terminal and run:" -ForegroundColor Yellow
    Write-Host "  .\setup-frontend.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to continue..."
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null