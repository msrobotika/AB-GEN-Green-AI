param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$ClosureDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage0_preflight_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$expectedC119TreeSha = "36621bbe2f43cf8da6bdb02df8fc2f19400112eb3d88d60bdf1f1f02c1484170"
$protocolCommit = "6519a7bbe42e9b8d183d27c1720257d1e7aae366"
$protocolUrl = "https://raw.githubusercontent.com/msrobotika/AB-GEN-Green-AI/$protocolCommit/FLYCORE_C1_20_PROTOCOL.md"
$expectedProtocolSha = "ada6024e4d1cb43ab750c0597d04c8e6186bea0b1e31010e26adb9edc70f8a03"

$resultsRoot = Join-Path $ProjectRoot "07_Resultados\Informes"
$c119Closure = Join-Path $resultsRoot "c1_19r_kmnist_transport_closure_v1"
$c119ClosureJson = Join-Path $c119Closure "closure.json"
$c119TreeShaFile = Join-Path $c119Closure "RUN_TREE_SHA256.txt"

function Assert-PathFile([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label NOT FOUND: $Path"
    }
}

function Assert-PathDir([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Label NOT FOUND: $Path"
    }
}

function Assert-DisjointRange(
    [int]$NewStart,
    [int]$NewEnd,
    [int]$OldStart,
    [int]$OldEnd,
    [string]$NewName,
    [string]$OldName
) {
    if (($NewStart -le $OldEnd) -and ($OldStart -le $NewEnd)) {
        throw "SEED COLLISION: $NewName [$NewStart..$NewEnd] overlaps $OldName [$OldStart..$OldEnd]"
    }
}

function Assert-DisjointValues(
    [int[]]$NewValues,
    [int[]]$OldValues,
    [string]$NewName,
    [string]$OldName
) {
    $old = @{}
    foreach ($v in $OldValues) { $old[$v] = $true }
    foreach ($v in $NewValues) {
        if ($old.ContainsKey($v)) {
            throw "SEED COLLISION: $NewName value $v overlaps $OldName"
        }
    }
}

Assert-PathDir $resultsRoot "RESULTS ROOT"
Assert-PathDir $c119Closure "C1.19 CLOSURE"
Assert-PathFile $c119ClosureJson "C1.19 CLOSURE.JSON"
Assert-PathFile $c119TreeShaFile "C1.19 RUN_TREE_SHA256"

if (Test-Path -LiteralPath $ClosureDir) {
    throw "C1.20 STAGE0 CLOSURE ALREADY EXISTS; refusing overwrite: $ClosureDir"
}

$c119ShaText = (Get-Content -LiteralPath $c119TreeShaFile -Raw).Trim()
if (-not $c119ShaText.StartsWith($expectedC119TreeSha)) {
    throw "C1.19 TREE SHA MISMATCH. EXPECTED $expectedC119TreeSha ; FOUND $c119ShaText"
}

$c119 = Get-Content -LiteralPath $c119ClosureJson -Raw | ConvertFrom-Json
if ($c119.status -ne "CLOSED_PASS") {
    throw "C1.19 STATUS IS NOT CLOSED_PASS: $($c119.status)"
}
if ($c119.tree_manifest_sha256 -ne $expectedC119TreeSha) {
    throw "C1.19 closure.json tree SHA mismatch: $($c119.tree_manifest_sha256)"
}
if ([int]$c119.complete_json_count -ne 160) {
    throw "C1.19 closure.json complete.json count mismatch: $($c119.complete_json_count)"
}
if ([int]$c119.model_pt_count -ne 160) {
    throw "C1.19 closure.json model.pt count mismatch: $($c119.model_pt_count)"
}

$c119RunDir = [string]$c119.run_dir
Assert-PathDir $c119RunDir "C1.19 RUN DIR"
$writableC119 = @(Get-ChildItem -LiteralPath $c119RunDir -File -Recurse | Where-Object { -not $_.IsReadOnly })
if ($writableC119.Count -ne 0) {
    throw "C1.19 IMMUTABILITY FAILURE: $($writableC119.Count) run files are writable"
}

$c120ExistingDirs = @(Get-ChildItem -LiteralPath $resultsRoot -Directory | Where-Object {
    $_.Name -match '^c1_20' -or $_.Name -match '^C1_20'
})
if ($c120ExistingDirs.Count -ne 0) {
    $names = ($c120ExistingDirs | ForEach-Object { $_.FullName }) -join "; "
    throw "PREMATURE C1.20 ARTIFACT DIRECTORY FOUND: $names"
}

$c120TopologyStart = 1830000
$c120TopologyEnd = 1830399
[int[]]$c120Training = @(1831001,1831002,1831003,1831004,1831005)
[int[]]$c120Damage = @(1832001,1832002,1832003,1832004)
[int[]]$c120Calibration = @(1833001)

Assert-DisjointRange $c120TopologyStart $c120TopologyEnd 950100 950399 "C1.20 topology" "C1.17B1 topology"
[int[]]$historicalTraining = @(42,123,777,1337,2026)
Assert-DisjointValues $c120Training $historicalTraining "C1.20 training" "historical training"

Assert-DisjointRange $c120TopologyStart $c120TopologyEnd 1810000 1810399 "C1.20 topology" "C1.18 development topology"
[int[]]$c118DevTraining = @(1811001,1811002,1811003,1811004,1811005)
[int[]]$c118DevDamage = @(1812001,1812002,1812003,1812004)
[int[]]$c118DevCalibration = @(1813001)
Assert-DisjointValues $c120Training $c118DevTraining "C1.20 training" "C1.18 development training"
Assert-DisjointValues $c120Damage $c118DevDamage "C1.20 damage" "C1.18 development damage"
Assert-DisjointValues $c120Calibration $c118DevCalibration "C1.20 calibration" "C1.18 development calibration"

Assert-DisjointRange $c120TopologyStart $c120TopologyEnd 1820000 1820399 "C1.20 topology" "C1.18/C1.19 confirmation topology"
[int[]]$c118ConfTraining = @(1821001,1821002,1821003,1821004,1821005)
[int[]]$c118ConfDamage = @(1822001,1822002,1822003,1822004)
[int[]]$c118ConfCalibration = @(1823001)
Assert-DisjointValues $c120Training $c118ConfTraining "C1.20 training" "C1.18/C1.19 training"
Assert-DisjointValues $c120Damage $c118ConfDamage "C1.20 damage" "C1.18/C1.19 damage"
Assert-DisjointValues $c120Calibration $c118ConfCalibration "C1.20 calibration" "C1.18/C1.19 calibration"

$tempProtocol = Join-Path ([System.IO.Path]::GetTempPath()) "c1_20_protocol_stage0.md"
if (Test-Path -LiteralPath $tempProtocol) {
    Remove-Item -LiteralPath $tempProtocol -Force
}

try {
    Invoke-WebRequest -UseBasicParsing -Uri $protocolUrl -OutFile $tempProtocol
    $actualProtocolSha = (Get-FileHash -LiteralPath $tempProtocol -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualProtocolSha -ne $expectedProtocolSha) {
        throw "C1.20 PROTOCOL SHA MISMATCH. EXPECTED $expectedProtocolSha ; FOUND $actualProtocolSha"
    }

    New-Item -ItemType Directory -Path $ClosureDir | Out-Null
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $lf = [char]10
    $tab = [char]9

    Copy-Item -LiteralPath $tempProtocol -Destination (Join-Path $ClosureDir "FLYCORE_C1_20_PROTOCOL.md")

    $seedManifest = [ordered]@{
        experiment = "C1.20P_STAGE0"
        status = "PROPOSED_NAMESPACE_AUDITED_DISJOINT"
        topology_candidates = [ordered]@{ start = $c120TopologyStart; end = $c120TopologyEnd; count = 400 }
        training_seeds = $c120Training
        damage_seeds = $c120Damage
        calibration_seed = 1833001
        calibration_n = 2048
        prior_namespaces_checked = @(
            "C1.17B1 topology 950100..950399",
            "historical training {42,123,777,1337,2026}",
            "C1.18 development 181xxxx",
            "C1.18 confirmation / C1.19 reuse 182xxxx"
        )
    }
    $seedJson = $seedManifest | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText((Join-Path $ClosureDir "seed_manifest.json"), $seedJson + $lf, $utf8NoBom)

    $preflight = [ordered]@{
        experiment = "C1.20P_STAGE0_INDEPENDENT_TOPOLOGY_TRANSPORT"
        status = "PASS_PRECHECK_ONLY"
        training = "NONE"
        performance = "NONE"
        topology_generation = "NONE"
        scientific_freeze = "NOT_YET"
        c1_19_status = "CLOSED_PASS"
        c1_19_run_tree_sha256 = $expectedC119TreeSha
        c1_19_run_files_read_only = $true
        c1_20_protocol_git_commit = $protocolCommit
        c1_20_protocol_sha256 = $expectedProtocolSha
        c1_20_protocol_state = "DRAFT_PRE_FREEZE_ONLY"
        seed_namespace_audit = "PASS"
        next_required_stage = "locate_and_hash_exact_structural_builder_and_prior_selected_topology_manifests; then build structural-only independent C1.20 bank before any training"
        authorization = "NO_TRAINING_NO_PERFORMANCE"
    }
    $preflightJson = $preflight | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText((Join-Path $ClosureDir "preflight.json"), $preflightJson + $lf, $utf8NoBom)

    $verify = @'
param(
    [string]$ClosureDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage0_preflight_v1"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$expectedFreeze = (Get-Content -LiteralPath (Join-Path $ClosureDir "STAGE0_FREEZE_SHA256.txt") -Raw).Trim().Split()[0].ToLowerInvariant()
$manifestPath = Join-Path $ClosureDir "stage0_manifest.tsv"
$manifestLines = @(Get-Content -LiteralPath $manifestPath)

foreach ($line in $manifestLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Split([char]9)
    if ($parts.Count -ne 3) { throw "INVALID MANIFEST ROW: $line" }
    $expectedSha = $parts[0]
    $expectedSize = [long]$parts[1]
    $rel = $parts[2]
    $full = Join-Path $ClosureDir $rel
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "MISSING: $rel" }
    $info = Get-Item -LiteralPath $full
    if ([long]$info.Length -ne $expectedSize) { throw "SIZE MISMATCH: $rel" }
    $sha = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sha -ne $expectedSha) { throw "SHA MISMATCH: $rel" }
}

$actualFreeze = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualFreeze -ne $expectedFreeze) {
    throw "STAGE0 FREEZE SHA MISMATCH. EXPECTED $expectedFreeze ; FOUND $actualFreeze"
}

$pre = Get-Content -LiteralPath (Join-Path $ClosureDir "preflight.json") -Raw | ConvertFrom-Json
if ($pre.training -ne "NONE" -or $pre.performance -ne "NONE" -or $pre.authorization -ne "NO_TRAINING_NO_PERFORMANCE") {
    throw "AUTHORIZATION BOUNDARY FAILED"
}

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE0 VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $actualFreeze"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "SCIENTIFIC FREEZE    : NOT YET"
Write-Host "NEXT                 : STRUCTURAL-BUILDER + PRIOR-TOPOLOGY MANIFEST LOCK"
Write-Host ("=" * 100)
'@
    [System.IO.File]::WriteAllText((Join-Path $ClosureDir "verify_only.ps1"), $verify.Trim() + $lf, $utf8NoBom)

    [string[]]$manifestFiles = @(
        "FLYCORE_C1_20_PROTOCOL.md",
        "seed_manifest.json",
        "preflight.json",
        "verify_only.ps1"
    )
    [Array]::Sort($manifestFiles, [System.StringComparer]::Ordinal)

    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($rel in $manifestFiles) {
        $full = Join-Path $ClosureDir $rel
        $info = Get-Item -LiteralPath $full
        $sha = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
        $lines.Add("$sha$tab$($info.Length)$tab$rel")
    }
    $manifestText = [string]::Join($lf, $lines) + $lf
    $manifestPath = Join-Path $ClosureDir "stage0_manifest.tsv"
    [System.IO.File]::WriteAllText($manifestPath, $manifestText, $utf8NoBom)

    $freezeSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText(
        (Join-Path $ClosureDir "STAGE0_FREEZE_SHA256.txt"),
        $freezeSha + "  stage0_manifest.tsv" + $lf,
        $utf8NoBom
    )

    Get-ChildItem -LiteralPath $ClosureDir -File | ForEach-Object { $_.IsReadOnly = $true }

    Write-Host ("=" * 100)
    Write-Host "PASS: C1.20P STAGE0 PRECHECK FROZEN"
    Write-Host "C1.19 TREE SHA256    : $expectedC119TreeSha"
    Write-Host "C1.19 READ-ONLY      : YES"
    Write-Host "PROTOCOL SHA256      : $expectedProtocolSha"
    Write-Host "SEED NAMESPACE       : DISJOINT PASS"
    Write-Host "TRAINING             : NONE"
    Write-Host "PERFORMANCE          : NONE"
    Write-Host "TOPOLOGY GENERATION  : NONE"
    Write-Host "SCIENTIFIC FREEZE    : NOT YET"
    Write-Host "STAGE0 FREEZE SHA256 : $freezeSha"
    Write-Host "CLOSURE DIR          : $ClosureDir"
    Write-Host "NEXT                 : LOCK EXACT STRUCTURAL BUILDER + PRIOR TOPOLOGY MANIFESTS"
    Write-Host ("=" * 100)
}
finally {
    if (Test-Path -LiteralPath $tempProtocol) {
        Remove-Item -LiteralPath $tempProtocol -Force -ErrorAction SilentlyContinue
    }
}
