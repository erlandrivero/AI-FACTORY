# Ensure we're in the project root
Set-Location (Split-Path $PSScriptRoot -Parent)

# Initialize git if needed
if (-not (Test-Path .git)) {
    Write-Output "Initializing git repository..."
    git init
}

# Add remote if not exists
$remote = git remote get-url origin 2>$null
if (-not $?) {
    Write-Output "Adding remote..."
    git remote add origin https://github.com/erlandrivero/AI-FACTORY.git
}

# Set main branch
git branch -M main

# Stage all files
Write-Output "Staging files..."
git add .

# Commit
Write-Output "Committing changes..."
git commit -m "Initial commit: AI Factory"

# Push
Write-Output "Pushing to GitHub..."
git push -u origin main
