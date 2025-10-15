# Ensure we're in the project root
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Output "Initializing Git repository..."
git init

Write-Output "Adding remote origin..."
git remote add origin https://github.com/erlandrivero/AI-FACTORY.git

Write-Output "Setting main branch..."
git branch -M main

Write-Output "Staging all files..."
git add .

Write-Output "Creating initial commit..."
git commit -m "Initial commit: AI Factory setup"

Write-Output "Pushing to GitHub..."
git push -u origin main

Write-Output "Done! Check your GitHub repository."
