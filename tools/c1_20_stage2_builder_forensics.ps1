param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage2_builder_forensics_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage1Freeze = "34f0cad1caca4e0032b5b2a40d098fc06b7e3742072188d43820aa6f7c5ce70b"
$Stage1FreezeFile = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage1_inventory_v1\STAGE1_FREEZE_SHA256.txt"

$Targets = @(
    [pscustomobject]@{ id="c1_18a_runner"; rel="00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\c1_18a_runner.py"; sha="19cb9848792373cc2612a4e494268e0e6c71bf4dc7d2ce1c292f2a1fa5758a28" },
    [pscustomobject]@{ id="c1_19r_recovery_runner"; rel="04_Codigo\training\c1_19r_recovery\c1_19r_recovery_runner.py"; sha="5522b3cc5a49aec7bd53282f1a54b2bc97f0194f9221124fbe7f664290d41929" },
    [pscustomobject]@{ id="recovery_evidence"; rel="04_Codigo\training\c1_19r_recovery\recovery_evidence.json"; sha="28d7b81ebeada8a78a0024a318d0e8f74595e0fa5cb695e99cb5fc95ec0ec1bd" },
    [pscustomobject]@{ id="selected_pairs_recovered"; rel="04_Codigo\training\c1_19r_recovery\selected_pairs_recovered.json"; sha="02a44ac1e21a14d1c64f2470f21f35cb8d70b7c32ff4acd0e4f9075d1c2df76b" },
    [pscustomobject]@{ id="c1_18a_ready_manifest"; rel="00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\C1_18A_READY_MANIFEST_2026-09-28.json"; sha="196a3e63451261bbd607794503a3042208d70025b64d37bfd8cd6543e727a21a" },
    [pscustomobject]@{ id="c1_18a_runner_lock"; rel="00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\c1_18a_runner_lock.json"; sha="f271c1958a7213d86f30ea7194e1dcb7a6e8d272a90356daa65872bf84645926" },
    [pscustomobject]@{ id="c1_18a_launch"; rel="00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\C1_18A_LAUNCH_2026-09-29.md"; sha="82a0d23e1d1a47553694b4157d44a6bdaa2936d72024b804211a383f2e4d307b" }
)

if (-not (Test-Path -LiteralPath $Stage1FreezeFile -PathType Leaf)) {
    throw "STAGE1 FREEZE FILE NOT FOUND: $Stage1FreezeFile"
}

$ObservedStage1 = (Get-Content -LiteralPath $Stage1FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage1 -ne $ExpectedStage1Freeze) {
    throw "STAGE1 FREEZE MISMATCH. EXPECTED $ExpectedStage1Freeze ; FOUND $ObservedStage1"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE2_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "FROZEN STAGE2 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}

foreach ($T in $Targets) {
    $Full = Join-Path $ProjectRoot $T.rel
    if (-not (Test-Path -LiteralPath $Full -PathType Leaf)) {
        throw "TARGET NOT FOUND: $($T.id) => $Full"
    }

    $ObservedSha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ObservedSha -ne $T.sha) {
        throw "TARGET SHA MISMATCH: $($T.id). EXPECTED $($T.sha) ; FOUND $ObservedSha"
    }
}

New-Item -ItemType Directory -Path $OutDir | Out-Null

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$StructuralRx = '(?i)(1820000|1820399|1810000|1810399|950100|950399|candidate|eligible|eligibility|pair|pairing|topolog|edge|RDE|delta_RDE|selection|selected|seed|hash|structur|build|generate)'
$StrongRx = '(?i)(1820000|1820399|400|91|16 pairs|32 topolog|eligible|eligibility|pairing|selected_pairs|delta_RDE|topology_hash|edge_hash|candidate_seeds)'

$EvidenceRows = @()
$FunctionRows = @()
$TargetRows = @()

foreach ($T in $Targets) {
    $Full = Join-Path $ProjectRoot $T.rel
    $Info = Get-Item -LiteralPath $Full
    $Text = [string](Get-Content -LiteralPath $Full -Raw)

    $TargetRows += [pscustomobject]@{
        id = $T.id
        path = $T.rel.Replace("\","/")
        sha256 = $T.sha
        bytes = [long]$Info.Length
    }

    $LineNo = 0
    foreach ($Line in ($Text -split "\r?\n")) {
        $LineNo++

        if ($Line -match $StructuralRx) {
            $Clean = $Line.Trim()
            if ($Clean.Length -gt 500) { $Clean = $Clean.Substring(0,500) }

            $EvidenceRows += [pscustomobject]@{
                id = $T.id
                line = [int]$LineNo
                strong = [bool]($Line -match $StrongRx)
                text = $Clean
            }
        }

        if ($T.rel -match '\.py$' -and $Line -match '^\s*(def|class)\s+[A-Za-z_][A-Za-z0-9_]*') {
            $FunctionRows += [pscustomobject]@{
                id = $T.id
                line = [int]$LineNo
                text = $Line.Trim()
            }
        }
    }
}

$TargetJson = [pscustomobject]@{
    experiment = "C1.20P_STAGE2_BUILDER_FORENSICS"
    status = "READ_ONLY_FORENSICS"
    stage1_freeze_sha256 = $ExpectedStage1Freeze
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    project_code_execution = "NONE"
    targets = @($TargetRows)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "targets.json"), (($TargetJson | ConvertTo-Json -Depth 6) + $LF), $Utf8)

$EvidenceLines = @("id" + $TAB + "line" + $TAB + "strong" + $TAB + "text")
foreach ($R in $EvidenceRows) {
    $Safe = ([string]$R.text).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $EvidenceLines += ([string]$R.id + $TAB + [string]$R.line + $TAB + [string]$R.strong + $TAB + $Safe)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "structural_evidence.tsv"), ([string]::Join($LF,$EvidenceLines) + $LF), $Utf8)

$FunctionLines = @("id" + $TAB + "line" + $TAB + "declaration")
foreach ($R in $FunctionRows) {
    $FunctionLines += ([string]$R.id + $TAB + [string]$R.line + $TAB + [string]$R.text)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "python_declarations.tsv"), ([string]::Join($LF,$FunctionLines) + $LF), $Utf8)

$StrongRows = @($EvidenceRows | Where-Object { $_.strong } | Sort-Object id,line)
$Report = @()
$Report += "# C1.20P Stage2 builder forensics"
$Report += ""
$Report += "STATUS: READ-ONLY FORENSICS"
$Report += ("Stage1 freeze: " + $ExpectedStage1Freeze)
$Report += "Training: NONE"
$Report += "Performance: NONE"
$Report += "Topology generation: NONE"
$Report += "Project-code execution: NONE"
$Report += ""
$Report += "## Strong structural evidence lines"
$Report += ""

foreach ($R in $StrongRows) {
    $Report += ("[" + [string]$R.id + ":" + [string]$R.line + "] " + [string]$R.text)
}

$Report += ""
$Report += "## Decision rule"
$Report += ""
$Report += "Do not promote a source to exact historical builder from filename alone. Promotion requires source-body evidence plus agreement with recovered structural invariants/manifests."

[System.IO.File]::WriteAllText((Join-Path $OutDir "FORENSIC_REPORT.md"), ([string]::Join($LF,$Report) + $LF), $Utf8)

$Verify = @'
param([string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage2_builder_forensics_v1")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage2_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE2_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage2_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE2_FREEZE_SHA256.txt" }

$Expected = (Get-Content -LiteralPath $Freeze -Raw).Trim().Split()[0].ToLowerInvariant()

foreach ($Row in @(Get-Content -LiteralPath $Manifest)) {
    if ([string]::IsNullOrWhiteSpace($Row)) { continue }

    $P = $Row.Split([char]9)
    if ($P.Count -ne 3) { throw "INVALID MANIFEST ROW: $Row" }

    $Full = Join-Path $OutDir $P[2]
    if (-not (Test-Path -LiteralPath $Full -PathType Leaf)) { throw "MISSING: $($P[2])" }

    $Info = Get-Item -LiteralPath $Full
    if ([long]$Info.Length -ne [long]$P[1]) { throw "SIZE MISMATCH: $($P[2])" }

    $Sha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Sha -ne $P[0]) { throw "SHA MISMATCH: $($P[2])" }
}

$Actual = (Get-FileHash -LiteralPath $Manifest -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $Expected) { throw "STAGE2 FREEZE MISMATCH" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "targets.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }
if ($I.project_code_execution -ne "NONE") { throw "CODE EXECUTION BOUNDARY FAILURE" }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE2 FORENSICS VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText((Join-Path $OutDir "verify_only.ps1"), ($Verify.Trim() + $LF), $Utf8)

$ManifestFiles = @(
    "FORENSIC_REPORT.md",
    "python_declarations.tsv",
    "structural_evidence.tsv",
    "targets.json",
    "verify_only.ps1"
)
[Array]::Sort($ManifestFiles,[System.StringComparer]::Ordinal)

$ManifestLines = @()
foreach ($Rel in $ManifestFiles) {
    $Full = Join-Path $OutDir $Rel
    $Info = Get-Item -LiteralPath $Full
    $Sha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    $ManifestLines += ($Sha + $TAB + [string]$Info.Length + $TAB + $Rel)
}

$ManifestPath = Join-Path $OutDir "stage2_manifest.tsv"
[System.IO.File]::WriteAllText($ManifestPath, ([string]::Join($LF,$ManifestLines) + $LF), $Utf8)

$Stage2Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText((Join-Path $OutDir "STAGE2_FREEZE_SHA256.txt"), ($Stage2Freeze + "  stage2_manifest.tsv" + $LF), $Utf8)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object { $_.IsReadOnly = $true }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE2 BUILDER FORENSICS FROZEN"
Write-Host "STAGE1 FREEZE SHA256 : $ExpectedStage1Freeze"
Write-Host "STAGE2 FREEZE SHA256 : $Stage2Freeze"
Write-Host "TARGETS              : $($Targets.Count)"
Write-Host "EVIDENCE LINES       : $($EvidenceRows.Count)"
Write-Host "STRONG LINES         : $($StrongRows.Count)"
Write-Host "FUNCTION/CLASS DECLS : $($FunctionRows.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host ("=" * 100)
