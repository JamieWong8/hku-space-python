param(
    [string]$FilePath = "C:\\Users\\jamie\\OneDrive\\Documents\\Deal Scout\\flask_app\\run_web_app.ps1"
)

if (!(Test-Path -LiteralPath $FilePath)) {
    Write-Error "File not found: $FilePath"
    exit 1
}

$null = $PSStyle.OutputRendering # noop to avoid PSCore warnings
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$errors)

if ($errors -and $errors.Count -gt 0) {
    Write-Host "Parse errors detected:" -ForegroundColor Red
    foreach ($e in $errors) {
        $start = $e.Extent.StartLineNumber
        $startCol = $e.Extent.StartColumnNumber
        $msg = $e.Message
        Write-Host ("Line {0}, Col {1}: {2}" -f $start, $startCol, $msg) -ForegroundColor Yellow
    }
    Write-Host "--- Context ---" -ForegroundColor Cyan
    $lines = Get-Content -LiteralPath $FilePath
    $context = @{}
    foreach ($e in $errors) {
        $ln = $e.Extent.StartLineNumber
        for ($i = [Math]::Max(1, $ln-2); $i -le [Math]::Min($lines.Length, $ln+2); $i++) {
            if (-not $context.ContainsKey($i)) { $context[$i] = $lines[$i-1] }
        }
    }
    foreach ($k in ($context.Keys | Sort-Object)) {
        Write-Host ("{0,4}: {1}" -f $k, $context[$k])
    }
    exit 2
} else {
    Write-Host "No parse errors found in: $FilePath" -ForegroundColor Green
    exit 0
}