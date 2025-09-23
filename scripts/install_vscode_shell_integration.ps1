# Installs VS Code's shell integration for PowerShell profiles (Windows PowerShell and PowerShell 7+)
# Safe: Only sources the script when TERM_PROGRAM == vscode
# Run from a PowerShell terminal in VS Code or externally with appropriate permissions

$ErrorActionPreference = 'Stop'

function Ensure-ProfileFile {
    param([string]$ProfilePath)
    $dir = Split-Path -Parent $ProfilePath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $ProfilePath)) { New-Item -ItemType File -Path $ProfilePath -Force | Out-Null }
}

function Add-VSCodeShellIntegration {
    param([string]$ProfilePath)
    $line = 'if ($env:TERM_PROGRAM -eq "vscode") { . "$(code --locate-shell-integration-path pwsh)" }'
    $content = Get-Content -LiteralPath $ProfilePath -ErrorAction SilentlyContinue
    if ($content -notcontains $line) {
        Add-Content -LiteralPath $ProfilePath -Value "`n# VS Code shell integration`n$line`n"
        Write-Host "Added VS Code shell integration to: $ProfilePath" -ForegroundColor Green
    } else {
        Write-Host "VS Code shell integration already present in: $ProfilePath" -ForegroundColor Yellow
    }
}

# Windows PowerShell (v5.1)
$winPsProfile = "$HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
Ensure-ProfileFile -ProfilePath $winPsProfile
Add-VSCodeShellIntegration -ProfilePath $winPsProfile

# PowerShell 7+ (pwsh)
$pwshProfile = "$HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1"
Ensure-ProfileFile -ProfilePath $pwshProfile
Add-VSCodeShellIntegration -ProfilePath $pwshProfile

Write-Host "Done. Restart VS Code terminals to activate shell integration." -ForegroundColor Cyan
