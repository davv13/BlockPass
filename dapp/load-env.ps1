<#
.SYNOPSIS
  Loads key=value lines from a .env file into the PowerShell process environment.

.PARAMETER DotEnvPath
  Path to the .env file (defaults to ".env" in the current directory).

.EXAMPLE
  # From your project root:
  .\load-env.ps1

  # Or specify a custom path:
  .\load-env.ps1 -DotEnvPath "../.env"
#>
param(
    [string]$DotEnvPath = ".env"
)

if (-not (Test-Path $DotEnvPath)) {
    Write-Error "Env file not found: $DotEnvPath"
    exit 1
}

Get-Content $DotEnvPath |
  Where-Object {
    $_.Trim() -ne '' -and -not $_.TrimStart().StartsWith('#')
  } |
  ForEach-Object {
    $parts = $_ -split '=', 2
    if ($parts.Count -eq 2) {
      $name  = $parts[0].Trim()
      $value = $parts[1].Trim()
      [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
      Write-Host "Loaded $name"
    }
  }
