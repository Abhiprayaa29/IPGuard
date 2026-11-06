param(
    [ValidateSet('start', 'stop', 'status')]
    [string]$Action = 'status'
)

$ErrorActionPreference = 'Stop'

$pgRoot = if ($env:IPGUARD_PG_ROOT) {
    $env:IPGUARD_PG_ROOT
} else {
    Join-Path $env:LOCALAPPDATA 'IPGuard\pgsql\17.11'
}
$dataDir = if ($env:IPGUARD_PGDATA) {
    $env:IPGUARD_PGDATA
} else {
    Join-Path $env:LOCALAPPDATA 'IPGuard\pgdata'
}
$logDir = if ($env:IPGUARD_PGLOG_DIR) {
    $env:IPGUARD_PGLOG_DIR
} else {
    Join-Path $env:LOCALAPPDATA 'IPGuard\logs'
}
$logFile = Join-Path $logDir 'postgresql.log'
$pgCtl = Join-Path $pgRoot 'bin\pg_ctl.exe'
$pgIsReady = Join-Path $pgRoot 'bin\pg_isready.exe'

if (-not (Test-Path -LiteralPath $pgCtl)) {
    throw "Portable PostgreSQL was not found at '$pgRoot'. Set IPGUARD_PG_ROOT, install PostgreSQL, or use docker compose."
}

switch ($Action) {
    'start' {
        & $pgIsReady -h 127.0.0.1 -p 5432 > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Output 'PostgreSQL is already available on 127.0.0.1:5432.'
            break
        }

        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Start-Process -FilePath $pgCtl -ArgumentList @(
            '-D', $dataDir,
            '-l', $logFile,
            'start'
        ) -WindowStyle Hidden | Out-Null

        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            & $pgIsReady -h 127.0.0.1 -p 5432 > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                break
            }
            Start-Sleep -Milliseconds 500
        }

        if (-not $ready) {
            Get-Content -LiteralPath $logFile -Tail 20 -ErrorAction SilentlyContinue
            throw 'PostgreSQL did not become ready on 127.0.0.1:5432.'
        }

        Write-Output 'PostgreSQL started on 127.0.0.1:5432.'
    }
    'stop' {
        & $pgIsReady -h 127.0.0.1 -p 5432 > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Output 'PostgreSQL is not running.'
            break
        }

        & $pgCtl -D $dataDir stop -m fast
        if ($LASTEXITCODE -ne 0) {
            throw 'PostgreSQL could not be stopped cleanly.'
        }
        Write-Output 'PostgreSQL stopped.'
    }
    'status' {
        & $pgCtl -D $dataDir status
        & $pgIsReady -h 127.0.0.1 -p 5432
        if ($LASTEXITCODE -ne 0) {
            exit 1
        }
    }
}
