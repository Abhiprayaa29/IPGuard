param(
    [string]$AndroidRoot = 'D:\Android',
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

$sdkRoot = Join-Path $AndroidRoot 'Sdk'
$jdkRoot = Join-Path $AndroidRoot 'jdk-17'
$gradleRoot = Join-Path $AndroidRoot 'gradle-8.13'
$gradleHome = Join-Path $AndroidRoot '.gradle'
$androidUserHome = Join-Path $AndroidRoot '.android'
$buildToolsRoot = Join-Path $sdkRoot 'build-tools\36.0.0'

$requiredPaths = @(
    (Join-Path $jdkRoot 'bin\java.exe'),
    (Join-Path $sdkRoot 'cmdline-tools\latest\bin\sdkmanager.bat'),
    (Join-Path $sdkRoot 'platform-tools\adb.exe'),
    (Join-Path $buildToolsRoot 'aapt2.exe'),
    (Join-Path $buildToolsRoot 'apksigner.bat'),
    (Join-Path $gradleRoot 'bin\gradle.bat')
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required Android tool was not found: $path"
    }
}

New-Item -ItemType Directory -Path $gradleHome -Force | Out-Null
New-Item -ItemType Directory -Path $androidUserHome -Force | Out-Null

$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$env:ANDROID_USER_HOME = $androidUserHome
$env:GRADLE_USER_HOME = $gradleHome
$env:JAVA_HOME = $jdkRoot

$pathEntries = @(
    (Join-Path $jdkRoot 'bin'),
    (Join-Path $sdkRoot 'cmdline-tools\latest\bin'),
    (Join-Path $sdkRoot 'platform-tools'),
    $buildToolsRoot,
    (Join-Path $gradleRoot 'bin')
)

$currentEntries = @($env:PATH -split ';' | Where-Object { $_ })
$missingEntries = @(
    $pathEntries | Where-Object { $currentEntries -notcontains $_ }
)
$env:PATH = (@($missingEntries) + $currentEntries) -join ';'

if (-not $Quiet) {
    Write-Output "ANDROID_HOME=$env:ANDROID_HOME"
    Write-Output "ANDROID_SDK_ROOT=$env:ANDROID_SDK_ROOT"
    Write-Output "ANDROID_USER_HOME=$env:ANDROID_USER_HOME"
    Write-Output "GRADLE_USER_HOME=$env:GRADLE_USER_HOME"
    Write-Output "JAVA_HOME=$env:JAVA_HOME"
}
