```powershell
param(
	[string] $RemoteUrl = "https://github.com/erlandrivero/AI-FACTORY.git",
	[string] $CommitMessage = "Initial commit: AI Factory"
)

# Resolve project root (script lives in scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

# Ensure git is available
try {
	git --version | Out-Null
} catch {
	Write-Error "Git is not installed or not on PATH. Install Git and re-run the script."
	exit 1
}

# Init repo if missing
if (-not (Test-Path ".git")) {
	Write-Output "Initializing git repository..."
	git init
} else {
	Write-Output "Git repository already initialized."
}

# Add or update origin remote
$existingRemote = $null
try { $existingRemote = git remote get-url origin 2>$null } catch {}
if ($existingRemote) {
	if ($existingRemote -ne $RemoteUrl) {
		Write-Output "Updating remote 'origin' URL..."
		git remote set-url origin $RemoteUrl
	} else {
		Write-Output "Remote 'origin' already set."
	}
} else {
	Write-Output "Adding remote 'origin'..."
	git remote add origin $RemoteUrl
}

# Ensure branch named 'main'
git branch -M main 2>$null

# Show status, stage all, and commit if needed
Write-Output "Current status:"
git status
Write-Output "`nStaging all files..."
git add .

$porcelain = git status --porcelain
if ($porcelain) {
	Write-Output "Committing changes..."
	git commit -m $CommitMessage
} else {
	Write-Output "No changes to commit."
}

# Push to origin main
Write-Output "Pushing to origin main (you may be prompted for credentials)..."
try {
	git push -u origin main
	Write-Output "Push complete."
} catch {
	Write-Error "Push failed. Check authentication (use Git credential manager or a GitHub PAT)."
	exit 1
}
```