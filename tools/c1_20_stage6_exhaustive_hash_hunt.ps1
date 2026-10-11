param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage6_exhaustive_hash_hunt_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage5Freeze = "2f71069a037ba10a495ed00ffcf9e302fb6d491c8cf530a77db84c82c3d79b70"
$Stage5FreezeFile = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage5_exact_source_search_v1\STAGE5_FREEZE_SHA256.txt"

$Targets = @{
    "C1.17B1_SOURCE" = "732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463"
    "C1.17B2_SOURCE" = "cd6be85673b156fa08ef05281bb5cae238e5781232c66866f08a87b223dd0dda"
    "C1.17B3_RUNNER" = "0ce6dfbef2d954b5cd89690deed309c62ee82043d17fe282ceb72fbfaf2f31a0"
    "C1.17B1_SELECTION_CANONICAL" = "21415db8372817c165306d70f6780cb33a79aa392a11f84ff52f3ff977cbbf22"
    "C1.17B2_FREEZE" = "072719d12f2816231ab193ef12bfb40dc7aeae7a0c28391f6aa455c44dbc6b2a"
    "C1.17B3_SUMMARY" = "183464a6f61e844dc6804be4e674ac2542331edfb7443515b14f8cd7fdd933d6"
    "C1.18_CONFIRMATION_SELECTION" = "ef653f07d1d712c70c789b2f93be08dd552d4fb37698a47374db13a1f81a300a"
    "C1.18_CONFIRMATION_CALIBRATION" = "5472743a6c8bc2598aa247a14c3d345d4d971ce982b5a545a51d72f6b04f2d82"
    "C1.18_CONFIRMATION_DAMAGE" = "84e8fbf7bf545b4f81a1075e25e7c02f6156236d9f5e96313f4fa5815c657b9d"
}

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "PROJECT ROOT NOT FOUND: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $Stage5FreezeFile -PathType Leaf)) {
    throw "STAGE5 FREEZE FILE NOT FOUND: $Stage5FreezeFile"
}

$ObservedStage5 = (Get-Content -LiteralPath $Stage5FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage5 -ne $ExpectedStage5Freeze) {
    throw "STAGE5 FREEZE MISMATCH. EXPECTED $ExpectedStage5Freeze ; FOUND $ObservedStage5"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE6_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "FROZEN STAGE6 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$Files = @(
    Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike ($OutDir + "*") }
)

$LooseHits = @()
$ZipHits = @()
$ZipRows = @()
$HashErrors = @()

foreach ($File in $Files) {
    $Rel = $File.FullName.Substring($ProjectRoot.Length).TrimStart("\").Replace("\","/")
    $Sha = ""

    try {
        $Sha = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    catch {
        $HashErrors += [pscustomobject]@{
            kind = "loose"
            location = $Rel
            error = $_.Exception.Message
        }
        continue
    }

    foreach ($KV in $Targets.GetEnumerator()) {
        if ($Sha -eq $KV.Value) {
            $LooseHits += [pscustomobject]@{
                anchor = [string]$KV.Key
                sha256 = $Sha
                bytes = [long]$File.Length
                path = $Rel
            }
        }
    }

    if ($File.Extension -ieq ".zip") {
        $ZipRows += [pscustomobject]@{
            path = $Rel
            sha256 = $Sha
            bytes = [long]$File.Length
        }
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$ZipEntriesHashed = 0

foreach ($ZipRow in $ZipRows) {
    $ZipPath = Join-Path $ProjectRoot ($ZipRow.path.Replace("/","\"))
    $Zip = $null

    try {
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

        foreach ($Entry in $Zip.Entries) {
            if ([string]::IsNullOrWhiteSpace($Entry.Name)) {
                continue
            }

            $Stream = $null
            $ShaObj = $null

            try {
                $Stream = $Entry.Open()
                $ShaObj = [System.Security.Cryptography.SHA256]::Create()
                $Bytes = $ShaObj.ComputeHash($Stream)
                $EntrySha = ([System.BitConverter]::ToString($Bytes)).Replace("-","").ToLowerInvariant()
                $ZipEntriesHashed++

                foreach ($KV in $Targets.GetEnumerator()) {
                    if ($EntrySha -eq $KV.Value) {
                        $ZipHits += [pscustomobject]@{
                            anchor = [string]$KV.Key
                            sha256 = $EntrySha
                            bytes = [long]$Entry.Length
                            archive = [string]$ZipRow.path
                            entry = [string]$Entry.FullName
                        }
                    }
                }
            }
            catch {
                $HashErrors += [pscustomobject]@{
                    kind = "zip_entry"
                    location = ([string]$ZipRow.path + "::" + [string]$Entry.FullName)
                    error = $_.Exception.Message
                }
            }
            finally {
                if ($ShaObj -ne $null) { $ShaObj.Dispose() }
                if ($Stream -ne $null) { $Stream.Dispose() }
            }
        }
    }
    catch {
        $HashErrors += [pscustomobject]@{
            kind = "zip_open"
            location = [string]$ZipRow.path
            error = $_.Exception.Message
        }
    }
    finally {
        if ($Zip -ne $null) { $Zip.Dispose() }
    }
}

New-Item -ItemType Directory -Path $OutDir | Out-Null

$TargetLines = @("anchor" + $TAB + "sha256")
foreach ($KV in ($Targets.GetEnumerator() | Sort-Object Key)) {
    $TargetLines += ([string]$KV.Key + $TAB + [string]$KV.Value)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "targets.tsv"),
    ([string]::Join($LF,$TargetLines) + $LF),
    $Utf8
)

$HitLines = @("source" + $TAB + "anchor" + $TAB + "sha256" + $TAB + "bytes" + $TAB + "location")
foreach ($R in ($LooseHits | Sort-Object anchor,path)) {
    $HitLines += ("loose" + $TAB + [string]$R.anchor + $TAB + [string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.path)
}
foreach ($R in ($ZipHits | Sort-Object anchor,archive,entry)) {
    $HitLines += ("zip" + $TAB + [string]$R.anchor + $TAB + [string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.archive + "::" + [string]$R.entry)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "exact_hits.tsv"),
    ([string]::Join($LF,$HitLines) + $LF),
    $Utf8
)

$ZipLines = @("sha256" + $TAB + "bytes" + $TAB + "path")
foreach ($R in ($ZipRows | Sort-Object path)) {
    $ZipLines += ([string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.path)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "zip_inventory.tsv"),
    ([string]::Join($LF,$ZipLines) + $LF),
    $Utf8
)

$ErrorLines = @("kind" + $TAB + "location" + $TAB + "error")
foreach ($R in $HashErrors) {
    $Safe = ([string]$R.error).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $ErrorLines += ([string]$R.kind + $TAB + [string]$R.location + $TAB + $Safe)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "hash_errors.tsv"),
    ([string]::Join($LF,$ErrorLines) + $LF),
    $Utf8
)

$State = [pscustomobject]@{
    experiment = "C1.20P_STAGE6_EXHAUSTIVE_HASH_HUNT"
    status = "READ_ONLY_HASH_ONLY"
    stage5_freeze_sha256 = $ExpectedStage5Freeze
    target_hashes = [int]$Targets.Count
    loose_files_hashed = [int]($Files.Count - @($HashErrors | Where-Object { $_.kind -eq "loose" }).Count)
    zip_archives_found = [int]$ZipRows.Count
    zip_entries_hashed = [int]$ZipEntriesHashed
    loose_exact_hits = [int]$LooseHits.Count
    zip_exact_hits = [int]$ZipHits.Count
    hash_errors = [int]$HashErrors.Count
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    project_code_execution = "NONE"
    archive_extraction = "NONE"
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "state.json"),
    (($State | ConvertTo-Json -Depth 5) + $LF),
    $Utf8
)

$Report = @()
$Report += "# C1.20P Stage6 exhaustive exact-hash hunt"
$Report += ""
$Report += "STATUS: READ-ONLY HASH-ONLY"
$Report += ("Stage5 freeze: " + $ExpectedStage5Freeze)
$Report += ("Target hashes: " + [string]$Targets.Count)
$Report += ("Loose files enumerated: " + [string]$Files.Count)
$Report += ("ZIP archives found: " + [string]$ZipRows.Count)
$Report += ("ZIP entries hashed: " + [string]$ZipEntriesHashed)
$Report += ("Loose exact hits: " + [string]$LooseHits.Count)
$Report += ("ZIP exact hits: " + [string]$ZipHits.Count)
$Report += ("Hash errors: " + [string]$HashErrors.Count)
$Report += "Training: NONE"
$Report += "Performance: NONE"
$Report += "Topology generation: NONE"
$Report += "Project-code execution: NONE"
$Report += "Archive extraction: NONE"
$Report += ""
$Report += "## Exact hits"
$Report += ""

if (($LooseHits.Count + $ZipHits.Count) -eq 0) {
    $Report += "NONE"
}
else {
    foreach ($R in ($LooseHits | Sort-Object anchor,path)) {
        $Report += ("LOOSE " + [string]$R.anchor + " | " + [string]$R.path + " | SHA256=" + [string]$R.sha256)
    }
    foreach ($R in ($ZipHits | Sort-Object anchor,archive,entry)) {
        $Report += ("ZIP " + [string]$R.anchor + " | " + [string]$R.archive + "::" + [string]$R.entry + " | SHA256=" + [string]$R.sha256)
    }
}

$Report += ""
$Report += "## Recovery boundary"
$Report += ""
$Report += "If this exhaustive all-tree/all-ZIP exact-hash pass returns zero hits with zero hash errors, the listed historical/confirmation artifacts are not present byte-identically in the current C:\ABGEN evidence tree. That closes byte-exact recovery for these anchors without implying that no semantically equivalent reconstruction exists."

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "EXHAUSTIVE_HASH_REPORT.md"),
    ([string]::Join($LF,$Report) + $LF),
    $Utf8
)

$Verify = @'
param([string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage6_exhaustive_hash_hunt_v1")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage6_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE6_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage6_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE6_FREEZE_SHA256.txt" }

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
if ($Actual -ne $Expected) { throw "STAGE6 FREEZE MISMATCH" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "state.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }
if ($I.project_code_execution -ne "NONE") { throw "CODE EXECUTION BOUNDARY FAILURE" }
if ($I.archive_extraction -ne "NONE") { throw "ARCHIVE EXTRACTION BOUNDARY FAILURE" }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE6 EXHAUSTIVE HASH VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "TARGET HASHES        : $($I.target_hashes)"
Write-Host "LOOSE FILES HASHED   : $($I.loose_files_hashed)"
Write-Host "ZIP ARCHIVES FOUND   : $($I.zip_archives_found)"
Write-Host "ZIP ENTRIES HASHED   : $($I.zip_entries_hashed)"
Write-Host "LOOSE EXACT HITS     : $($I.loose_exact_hits)"
Write-Host "ZIP EXACT HITS       : $($I.zip_exact_hits)"
Write-Host "HASH ERRORS          : $($I.hash_errors)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "verify_only.ps1"),
    ($Verify.Trim() + $LF),
    $Utf8
)

$ManifestFiles = @(
    "EXHAUSTIVE_HASH_REPORT.md",
    "exact_hits.tsv",
    "hash_errors.tsv",
    "state.json",
    "targets.tsv",
    "verify_only.ps1",
    "zip_inventory.tsv"
)
[Array]::Sort($ManifestFiles,[System.StringComparer]::Ordinal)

$ManifestLines = @()
foreach ($Rel in $ManifestFiles) {
    $Full = Join-Path $OutDir $Rel
    $Info = Get-Item -LiteralPath $Full
    $Sha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    $ManifestLines += ($Sha + $TAB + [string]$Info.Length + $TAB + $Rel)
}

$ManifestPath = Join-Path $OutDir "stage6_manifest.tsv"
[System.IO.File]::WriteAllText(
    $ManifestPath,
    ([string]::Join($LF,$ManifestLines) + $LF),
    $Utf8
)

$Stage6Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "STAGE6_FREEZE_SHA256.txt"),
    ($Stage6Freeze + "  stage6_manifest.tsv" + $LF),
    $Utf8
)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object { $_.IsReadOnly = $true }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE6 EXHAUSTIVE HASH HUNT FROZEN"
Write-Host "STAGE5 FREEZE SHA256 : $ExpectedStage5Freeze"
Write-Host "STAGE6 FREEZE SHA256 : $Stage6Freeze"
Write-Host "TARGET HASHES        : $($Targets.Count)"
Write-Host "LOOSE FILES ENUM     : $($Files.Count)"
Write-Host "ZIP ARCHIVES FOUND   : $($ZipRows.Count)"
Write-Host "ZIP ENTRIES HASHED   : $ZipEntriesHashed"
Write-Host "LOOSE EXACT HITS     : $($LooseHits.Count)"
Write-Host "ZIP EXACT HITS       : $($ZipHits.Count)"
Write-Host "HASH ERRORS          : $($HashErrors.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
