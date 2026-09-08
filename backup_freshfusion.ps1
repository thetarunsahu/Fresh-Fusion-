param(
    [switch]$IncludeUploads
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupRoot = Join-Path $Root '.runtime\backups'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$stage = Join-Path $BackupRoot "stage-$stamp"
$zip = Join-Path $BackupRoot "FreshFusion-backup-$stamp.zip"

New-Item -ItemType Directory -Force -Path $stage | Out-Null

try {
    $copied = @()
    foreach ($candidate in @(
        (Join-Path $Root 'freshfusion.db'),
        (Join-Path $Root 'backend\freshfusion.db')
    )) {
        if (Test-Path $candidate) {
            Copy-Item $candidate -Destination $stage -Force
            $copied += $candidate
        }
    }

    if ($IncludeUploads) {
        $uploads = Join-Path $Root 'uploads'
        if (Test-Path $uploads) {
            Copy-Item $uploads -Destination (Join-Path $stage 'uploads') -Recurse -Force
            $copied += $uploads
        }
    }

    if (-not $copied.Count) {
        throw 'No FreshFusion database was found. Start the backend once before creating a database backup.'
    }

    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force

    Write-Host ''
    Write-Host 'FreshFusion backup created.' -ForegroundColor Green
    Write-Host "Archive: $zip" -ForegroundColor Cyan
    Write-Host 'Included:' -ForegroundColor White
    $copied | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    if (-not $IncludeUploads) {
        Write-Host 'Uploads were not included. Use -IncludeUploads when a full evidence backup is needed.' -ForegroundColor Yellow
    }
    Write-Host ''
}
finally {
    Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
}
