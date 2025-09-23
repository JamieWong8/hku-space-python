param([string]$FilePath)
if(!(Test-Path -LiteralPath $FilePath)) { Write-Error "File not found: $FilePath"; exit 1 }
$i=1
Get-Content -LiteralPath $FilePath | ForEach-Object { "{0,4}: {1}" -f $i, $_; $i++ }