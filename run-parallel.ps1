[CmdletBinding()]
param(
    [string]$InputFile = (Join-Path $PSScriptRoot 'cmd2.txt'),
    [int]$MaxConcurrency = 50
)

if ($MaxConcurrency -lt 1) {
    throw 'MaxConcurrency must be at least 1.'
}
if (-not (Test-Path -LiteralPath $InputFile)) {
    throw "Input file not found: $InputFile"
}

# UTF-8 matches the command file in this directory. Use -Encoding Default if the file is GBK.
$commands = @(
    Get-Content -LiteralPath $InputFile -Encoding UTF8 |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and -not $_.StartsWith('#') }
)

if ($commands.Count -eq 0) {
    Write-Host 'No commands found.'
    exit 0
}

$worker = {
    param([int]$Index, [string]$Command, [string]$WorkingDirectory)

    try {
        Set-Location -LiteralPath $WorkingDirectory
        # Run through cmd.exe so cmd redirection (>) and cmd syntax work unchanged.
        $output = @(& cmd.exe /d /s /c $Command 2>&1)
        $text = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        [pscustomobject]@{
            Index    = $Index
            Command  = $Command
            ExitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
            Output   = $text
            Error    = ''
        }
    }
    catch {
        [pscustomobject]@{
            Index    = $Index
            Command  = $Command
            ExitCode = -1
            Output   = ''
            Error    = $_.Exception.Message
        }
    }
}

$jobs = @()
$results = @()
$next = 0

while (($next -lt $commands.Count) -or ($jobs.Count -gt 0)) {
    while (($next -lt $commands.Count) -and ($jobs.Count -lt $MaxConcurrency)) {
        $jobs += Start-Job -ScriptBlock $worker -ArgumentList ($next + 1), $commands[$next], $PSScriptRoot
        $next++
    }

    if ($jobs.Count -gt 0) {
        Wait-Job -Job $jobs -Any | Out-Null
        $finished = @($jobs | Where-Object { $_.State -in @('Completed', 'Failed', 'Stopped') })
        foreach ($job in $finished) {
            $received = @(Receive-Job -Job $job -ErrorAction SilentlyContinue)
            if ($received.Count -gt 0) {
                $results += $received
            } else {
                $results += [pscustomobject]@{
                    Index = 0; Command = ''; ExitCode = -1; Output = ''
                    Error = "Job $($job.Id) ended in state $($job.State)."
                }
            }
            Remove-Job -Job $job -Force
            $jobs = @($jobs | Where-Object { $_.Id -ne $job.Id })
        }
    }
}

$results = @($results | Sort-Object Index)
$summaryPath = Join-Path (Split-Path -Parent $InputFile) 'run-summary.csv'
$results | Select-Object Index, ExitCode, Command, Error, Output |
    Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding UTF8

$failed = @($results | Where-Object { $_.ExitCode -ne 0 })
Write-Host "Finished $($results.Count) command(s); failed: $($failed.Count)."
Write-Host "Summary: $summaryPath"

if ($failed.Count -gt 0) {
    exit 1
}
