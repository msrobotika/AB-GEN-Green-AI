param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage5_exact_source_search_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage4Freeze = "6fc6136bb9e937e5acbfb781740b401d6a77c8a94001d105814ec071e4215f6a"
$Stage4FreezeFile = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage4_zip_builder_audit_v1\STAGE4_FREEZE_SHA256.txt"

$KnownHashes = @{
    "C1.17B1_SOURCE" = "732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463"
    "C1.17B2_SOURCE" = "cd6be85673b156fa08ef05281bb5cae238e5781232c66866f08a87b223dd0dda"
    "C1.17B3_RUNNER" = "0ce6dfbef2d954b5cd89690deed309c62ee82043d17fe282ceb72fbfaf2f31a0"
    "C1.17B1_SELECTION_CANONICAL" = "21415db8372817c165306d70f6780cb33a79aa392a11f84ff52f3ff977cbbf22"
    "C1.17B2_FREEZE" = "072719d12f2816231ab193ef12bfb40dc7aeae7a0c28391f6aa455c44dbc6b2a"
    "C1.17B3_SUMMARY" = "183464a6f61e844dc6804be4e674ac2542331edfb7443515b14f8cd7fdd933d6"
}

if (-not (Test-Path -LiteralPath $Stage4FreezeFile -PathType Leaf)) {
    throw "STAGE4 FREEZE FILE NOT FOUND: $Stage4FreezeFile"
}

$ObservedStage4 = (Get-Content -LiteralPath $Stage4FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage4 -ne $ExpectedStage4Freeze) {
    throw "STAGE4 FREEZE MISMATCH. EXPECTED $ExpectedStage4Freeze ; FOUND $ObservedStage4"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE5_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "FROZEN STAGE5 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutDir | Out-Null

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$SearchRoots = @(
    (Join-Path $ProjectRoot "00_Backup_Drive"),
    (Join-Path $ProjectRoot "04_Codigo\training"),
    (Join-Path $ProjectRoot "07_Resultados\Informes")
)

$AllowedExts = @(".py",".ps1",".json",".md",".txt",".csv",".tsv",".yaml",".yml",".zip")
$ExcludeRx = '(?i)(\\\.venv\\|\\__pycache__\\|\\c1_19r_kmnist_transport_run\\|\\c1_20p_stage[0-9])'
$ContentRx = '(?i)(c1_17b1_independent_bank|c1_18p_dev_bank|c1_18p_dev_bank_derivation|1820000|1820399|16 pairs|32 topologies|target_pairs.{0,20}16|target_topologies.{0,20}32|confirmation|confirmatory|derived builder|selected_pairs)'
$NameRx = '(?i)(c1_17b1|c1_18p|confirm|builder|bank|derivation|selected_pairs)'

$LooseExactHits = @()
$LooseTextHits = @()
$ZipExactHits = @()
$ZipTextHits = @()
$ZipEntryInventory = @()
$ZipRows = @()

$LooseFiles = @()
foreach ($Root in $SearchRoots) {
    if (Test-Path -LiteralPath $Root -PathType Container) {
        $LooseFiles += @(
            Get-ChildItem -LiteralPath $Root -File -Recurse |
            Where-Object {
                ($AllowedExts -contains $_.Extension.ToLowerInvariant()) -and
                ($_.FullName -notmatch $ExcludeRx)
            }
        )
    }
}

foreach ($File in $LooseFiles) {
    $Ext = $File.Extension.ToLowerInvariant()
    $Rel = $File.FullName.Substring($ProjectRoot.Length).TrimStart("\").Replace("\","/")

    if ($Ext -eq ".zip") {
        $ZipRows += [pscustomobject]@{
            path = $Rel
            bytes = [long]$File.Length
            sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        continue
    }

    $Sha = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()

    foreach ($KV in $KnownHashes.GetEnumerator()) {
        if ($Sha -eq $KV.Value) {
            $LooseExactHits += [pscustomobject]@{
                anchor = [string]$KV.Key
                sha256 = $Sha
                path = $Rel
            }
        }
    }

    $NameMatch = ($Rel -match $NameRx)
    $Text = ""
    $ContentMatch = $false

    if ($File.Length -le 10485760) {
        try {
            $Text = [string](Get-Content -LiteralPath $File.FullName -Raw)
            $ContentMatch = ($Text -match $ContentRx)
        }
        catch {
            $Text = ""
            $ContentMatch = $false
        }
    }

    if ($NameMatch -or $ContentMatch) {
        $Evidence = @()
        if (-not [string]::IsNullOrEmpty($Text)) {
            $LineNo = 0
            foreach ($Line in ($Text -split "\r?\n")) {
                $LineNo++
                if ($Line -match $ContentRx) {
                    $Clean = $Line.Trim()
                    if ($Clean.Length -gt 400) { $Clean = $Clean.Substring(0,400) }
                    if ($Evidence.Count -lt 12) {
                        $Evidence += ("L" + [string]$LineNo + ": " + $Clean)
                    }
                }
            }
        }

        $LooseTextHits += [pscustomobject]@{
            path = $Rel
            sha256 = $Sha
            bytes = [long]$File.Length
            evidence = [string]::Join(" || ", $Evidence)
        }
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

foreach ($ZipRow in $ZipRows) {
    $ZipPath = Join-Path $ProjectRoot ($ZipRow.path.Replace("/","\"))
    $Zip = $null

    try {
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

        foreach ($Entry in $Zip.Entries) {
            if ([string]::IsNullOrWhiteSpace($Entry.Name)) { continue }

            $HashStream = $null
            $ShaObj = $null
            $EntrySha = ""

            try {
                $HashStream = $Entry.Open()
                $ShaObj = [System.Security.Cryptography.SHA256]::Create()
                $HashBytes = $ShaObj.ComputeHash($HashStream)
                $EntrySha = ([System.BitConverter]::ToString($HashBytes)).Replace("-","").ToLowerInvariant()
            }
            finally {
                if ($ShaObj -ne $null) { $ShaObj.Dispose() }
                if ($HashStream -ne $null) { $HashStream.Dispose() }
            }

            $ZipEntryInventory += [pscustomobject]@{
                archive = $ZipRow.path
                entry = $Entry.FullName
                sha256 = $EntrySha
                bytes = [long]$Entry.Length
            }

            foreach ($KV in $KnownHashes.GetEnumerator()) {
                if ($EntrySha -eq $KV.Value) {
                    $ZipExactHits += [pscustomobject]@{
                        anchor = [string]$KV.Key
                        sha256 = $EntrySha
                        archive = $ZipRow.path
                        entry = $Entry.FullName
                    }
                }
            }

            $Ext = [System.IO.Path]::GetExtension($Entry.Name).ToLowerInvariant()
            if (-not ($AllowedExts -contains $Ext)) { continue }
            if ($Entry.Length -gt 10485760) { continue }

            $EntryNameMatch = ($Entry.FullName -match $NameRx)
            $ReadStream = $null
            $Reader = $null
            $Text = ""

            try {
                $ReadStream = $Entry.Open()
                $Reader = New-Object System.IO.StreamReader($ReadStream, [System.Text.Encoding]::UTF8, $true)
                $Text = $Reader.ReadToEnd()
            }
            finally {
                if ($Reader -ne $null) { $Reader.Dispose() }
                elseif ($ReadStream -ne $null) { $ReadStream.Dispose() }
            }

            $EntryContentMatch = ($Text -match $ContentRx)
            if (-not ($EntryNameMatch -or $EntryContentMatch)) { continue }

            $Evidence = @()
            $LineNo = 0
            foreach ($Line in ($Text -split "\r?\n")) {
                $LineNo++
                if ($Line -match $ContentRx) {
                    $Clean = $Line.Trim()
                    if ($Clean.Length -gt 400) { $Clean = $Clean.Substring(0,400) }
                    if ($Evidence.Count -lt 14) {
                        $Evidence += ("L" + [string]$LineNo + ": " + $Clean)
                    }
                }
            }

            $ZipTextHits += [pscustomobject]@{
                archive = $ZipRow.path
                entry = $Entry.FullName
                sha256 = $EntrySha
                bytes = [long]$Entry.Length
                evidence = [string]::Join(" || ", $Evidence)
            }
        }
    }
    finally {
        if ($Zip -ne $null) { $Zip.Dispose() }
    }
}

$LooseTextHits = @($LooseTextHits | Sort-Object path)
$ZipTextHits = @($ZipTextHits | Sort-Object archive,entry)
$ZipEntryInventory = @($ZipEntryInventory | Sort-Object archive,entry)

$ExactLines = @("source" + $TAB + "anchor" + $TAB + "sha256" + $TAB + "location")
foreach ($R in $LooseExactHits) {
    $ExactLines += ("loose" + $TAB + [string]$R.anchor + $TAB + [string]$R.sha256 + $TAB + [string]$R.path)
}
foreach ($R in $ZipExactHits) {
    $ExactLines += ("zip" + $TAB + [string]$R.anchor + $TAB + [string]$R.sha256 + $TAB + [string]$R.archive + "::" + [string]$R.entry)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "exact_hash_hits.tsv"), ([string]::Join($LF,$ExactLines) + $LF), $Utf8)

$LooseLines = @("sha256" + $TAB + "bytes" + $TAB + "path" + $TAB + "evidence")
foreach ($R in $LooseTextHits) {
    $Safe = ([string]$R.evidence).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $LooseLines += ([string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.path + $TAB + $Safe)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "loose_text_hits.tsv"), ([string]::Join($LF,$LooseLines) + $LF), $Utf8)

$ZipHitLines = @("sha256" + $TAB + "bytes" + $TAB + "archive" + $TAB + "entry" + $TAB + "evidence")
foreach ($R in $ZipTextHits) {
    $Safe = ([string]$R.evidence).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $ZipHitLines += ([string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.archive + $TAB + [string]$R.entry + $TAB + $Safe)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "zip_text_hits.tsv"), ([string]::Join($LF,$ZipHitLines) + $LF), $Utf8)

$InventoryLines = @("sha256" + $TAB + "bytes" + $TAB + "archive" + $TAB + "entry")
foreach ($R in $ZipEntryInventory) {
    $InventoryLines += ([string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.archive + $TAB + [string]$R.entry)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "zip_entry_inventory.tsv"), ([string]::Join($LF,$InventoryLines) + $LF), $Utf8)

$State = [pscustomobject]@{
    experiment = "C1.20P_STAGE5_EXACT_SOURCE_SEARCH"
    status = "READ_ONLY_EXACT_SOURCE_SEARCH"
    stage4_freeze_sha256 = $ExpectedStage4Freeze
    loose_files_scanned = [int]$LooseFiles.Count
    zip_archives = [int]$ZipRows.Count
    zip_entries_hashed = [int]$ZipEntryInventory.Count
    loose_exact_hash_hits = [int]$LooseExactHits.Count
    zip_exact_hash_hits = [int]$ZipExactHits.Count
    loose_text_hits = [int]$LooseTextHits.Count
    zip_text_hits = [int]$ZipTextHits.Count
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    project_code_execution = "NONE"
    archive_extraction = "NONE"
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "state.json"), (($State | ConvertTo-Json -Depth 5) + $LF), $Utf8)

$Report = @()
$Report += "# C1.20P Stage5 exact source search"
$Report += ""
$Report += "STATUS: READ-ONLY EXACT SOURCE SEARCH"
$Report += ("Stage4 freeze: " + $ExpectedStage4Freeze)
$Report += ("Loose files scanned: " + [string]$LooseFiles.Count)
$Report += ("ZIP archives: " + [string]$ZipRows.Count)
$Report += ("ZIP entries hashed: " + [string]$ZipEntryInventory.Count)
$Report += ("Loose exact hash hits: " + [string]$LooseExactHits.Count)
$Report += ("ZIP exact hash hits: " + [string]$ZipExactHits.Count)
$Report += ("Loose text hits: " + [string]$LooseTextHits.Count)
$Report += ("ZIP text hits: " + [string]$ZipTextHits.Count)
$Report += "Training: NONE"
$Report += "Performance: NONE"
$Report += "Topology generation: NONE"
$Report += "Project-code execution: NONE"
$Report += "Archive extraction: NONE"
$Report += ""
$Report += "## Exact historical hash hits"
$Report += ""

if (($LooseExactHits.Count + $ZipExactHits.Count) -eq 0) {
    $Report += "NONE"
}
else {
    foreach ($R in $LooseExactHits) {
        $Report += ("LOOSE " + [string]$R.anchor + " | " + [string]$R.path + " | SHA256=" + [string]$R.sha256)
    }
    foreach ($R in $ZipExactHits) {
        $Report += ("ZIP " + [string]$R.anchor + " | " + [string]$R.archive + "::" + [string]$R.entry + " | SHA256=" + [string]$R.sha256)
    }
}

$Report += ""
$Report += "## High-value loose text hits"
$Report += ""

foreach ($R in ($LooseTextHits | Select-Object -First 30)) {
    $Report += ([string]$R.path + " | SHA256=" + [string]$R.sha256)
    if (-not [string]::IsNullOrWhiteSpace([string]$R.evidence)) {
        $Report += [string]$R.evidence
    }
    $Report += ""
}

$Report += "## High-value ZIP text hits"
$Report += ""

foreach ($R in ($ZipTextHits | Select-Object -First 40)) {
    $Report += ([string]$R.archive + "::" + [string]$R.entry + " | SHA256=" + [string]$R.sha256)
    if (-not [string]::IsNullOrWhiteSpace([string]$R.evidence)) {
        $Report += [string]$R.evidence
    }
    $Report += ""
}

$Report += "## Decision boundary"
$Report += ""
$Report += "If the exact C1.17B1 source hash is found, bind and audit that source directly. If only derived/reconstructed descendants survive, do not relabel them historical. A later C1.20 builder may be derived only after provenance status and semantic locks are explicitly frozen."

[System.IO.File]::WriteAllText((Join-Path $OutDir "EXACT_SOURCE_REPORT.md"), ([string]::Join($LF,$Report) + $LF), $Utf8)

$Verify = @'
param([string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage5_exact_source_search_v1")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage5_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE5_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage5_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE5_FREEZE_SHA256.txt" }

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
if ($Actual -ne $Expected) { throw "STAGE5 FREEZE MISMATCH" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "state.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }
if ($I.project_code_execution -ne "NONE") { throw "CODE EXECUTION BOUNDARY FAILURE" }
if ($I.archive_extraction -ne "NONE") { throw "ARCHIVE EXTRACTION BOUNDARY FAILURE" }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE5 EXACT SOURCE VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "LOOSE FILES          : $($I.loose_files_scanned)"
Write-Host "ZIP ARCHIVES         : $($I.zip_archives)"
Write-Host "ZIP ENTRIES HASHED   : $($I.zip_entries_hashed)"
Write-Host "LOOSE EXACT HITS     : $($I.loose_exact_hash_hits)"
Write-Host "ZIP EXACT HITS       : $($I.zip_exact_hash_hits)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText((Join-Path $OutDir "verify_only.ps1"), ($Verify.Trim() + $LF), $Utf8)

$ManifestFiles = @(
    "EXACT_SOURCE_REPORT.md",
    "exact_hash_hits.tsv",
    "loose_text_hits.tsv",
    "state.json",
    "verify_only.ps1",
    "zip_entry_inventory.tsv",
    "zip_text_hits.tsv"
)
[Array]::Sort($ManifestFiles,[System.StringComparer]::Ordinal)

$ManifestLines = @()
foreach ($Rel in $ManifestFiles) {
    $Full = Join-Path $OutDir $Rel
    $Info = Get-Item -LiteralPath $Full
    $Sha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    $ManifestLines += ($Sha + $TAB + [string]$Info.Length + $TAB + $Rel)
}

$ManifestPath = Join-Path $OutDir "stage5_manifest.tsv"
[System.IO.File]::WriteAllText($ManifestPath, ([string]::Join($LF,$ManifestLines) + $LF), $Utf8)

$Stage5Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText((Join-Path $OutDir "STAGE5_FREEZE_SHA256.txt"), ($Stage5Freeze + "  stage5_manifest.tsv" + $LF), $Utf8)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object { $_.IsReadOnly = $true }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE5 EXACT SOURCE SEARCH FROZEN"
Write-Host "STAGE4 FREEZE SHA256 : $ExpectedStage4Freeze"
Write-Host "STAGE5 FREEZE SHA256 : $Stage5Freeze"
Write-Host "LOOSE FILES          : $($LooseFiles.Count)"
Write-Host "ZIP ARCHIVES         : $($ZipRows.Count)"
Write-Host "ZIP ENTRIES HASHED   : $($ZipEntryInventory.Count)"
Write-Host "LOOSE EXACT HITS     : $($LooseExactHits.Count)"
Write-Host "ZIP EXACT HITS       : $($ZipExactHits.Count)"
Write-Host "LOOSE TEXT HITS      : $($LooseTextHits.Count)"
Write-Host "ZIP TEXT HITS        : $($ZipTextHits.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
