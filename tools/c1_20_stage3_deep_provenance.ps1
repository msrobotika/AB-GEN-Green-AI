param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage3_deep_provenance_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage2Freeze = "672e96b10573e2b1b7dae50fc722f49b252b5339a0a67c257c72ce8059cf62d0"
$Stage2FreezeFile = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage2_builder_forensics_v1\STAGE2_FREEZE_SHA256.txt"

$KnownHashes = @{
    "C1.17B1_SOURCE" = "732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463"
    "C1.17B2_SOURCE" = "cd6be85673b156fa08ef05281bb5cae238e5781232c66866f08a87b223dd0dda"
    "C1.17B1_SELECTION_CANONICAL" = "21415db8372817c165306d70f6780cb33a79aa392a11f84ff52f3ff977cbbf22"
    "C1.18_RECOVERED_RUNNER" = "5522b3cc5a49aec7bd53282f1a54b2bc97f0194f9221124fbe7f664290d41929"
    "C1.18_RECOVERED_PAIRS" = "02a44ac1e21a14d1c64f2470f21f35cb8d70b7c32ff4acd0e4f9075d1c2df76b"
}

if (-not (Test-Path -LiteralPath $Stage2FreezeFile -PathType Leaf)) {
    throw "STAGE2 FREEZE FILE NOT FOUND: $Stage2FreezeFile"
}

$ObservedStage2 = (Get-Content -LiteralPath $Stage2FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage2 -ne $ExpectedStage2Freeze) {
    throw "STAGE2 FREEZE MISMATCH. EXPECTED $ExpectedStage2Freeze ; FOUND $ObservedStage2"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE3_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "FROZEN STAGE3 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}

New-Item -ItemType Directory -Path $OutDir | Out-Null

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$TextExts = @(".py",".ps1",".json",".md",".txt",".yaml",".yml",".toml",".ini",".csv",".tsv")
$NameRx = '(?i)(c1[_\.-]?(16|17|18|19)|flycore|topolog|structur|eligib|pair|selection|selected|bank|rde|confirm|candidate)'
$ContentRx = '(?i)(1820000|1820399|1810000|1810399|950100|950399|candidate_count|eligible_pair_count|selected_pairs|selected_pairs_snapshot|selected_pairs_recovered|delta_rde|eligib|pairing|pair_candidates|topology_sha256|edge_hash|build_flycore|candidate seed|candidate_seed|confirmation)'
$StrongRx = '(?i)(1820000|1820399|candidate_count.{0,30}400|eligible_pair_count.{0,30}91|selected_pairs_snapshot|selected_pairs_recovered|pairing|eligibility|eligible_pair|delta_rde|topology_sha256|candidate_seed|candidate seeds)'

$LooseHits = @()
$ZipHits = @()
$ArchiveRows = @()
$KnownHashHits = @()

$AllFiles = @(Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse)

foreach ($File in $AllFiles) {
    $Rel = $File.FullName.Substring($ProjectRoot.Length).TrimStart("\").Replace("\","/")
    $Ext = $File.Extension.ToLowerInvariant()

    if ($Ext -eq ".zip") {
        $ArchiveRows += [pscustomobject]@{
            archive = $Rel
            bytes = [long]$File.Length
            sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        continue
    }

    if (-not ($TextExts -contains $Ext)) {
        continue
    }

    $NameMatch = ($Rel -match $NameRx)
    $Text = ""
    $ContentMatch = $false

    if ($File.Length -le 5242880) {
        try {
            $Text = [string](Get-Content -LiteralPath $File.FullName -Raw)
            $ContentMatch = ($Text -match $ContentRx)
        }
        catch {
            $Text = ""
            $ContentMatch = $false
        }
    }

    if (-not ($NameMatch -or $ContentMatch)) {
        continue
    }

    $Sha = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $Anchors = @()

    foreach ($KV in $KnownHashes.GetEnumerator()) {
        if ($Sha -eq $KV.Value) {
            $Anchors += [string]$KV.Key
            $KnownHashHits += [pscustomobject]@{
                source = "loose"
                anchor = [string]$KV.Key
                sha256 = $Sha
                location = $Rel
            }
        }
    }

    $StrongCount = 0
    $Evidence = @()
    if (-not [string]::IsNullOrEmpty($Text)) {
        $LineNo = 0
        foreach ($Line in ($Text -split "\r?\n")) {
            $LineNo++
            if ($Line -match $StrongRx) {
                $StrongCount++
                $Clean = $Line.Trim()
                if ($Clean.Length -gt 350) { $Clean = $Clean.Substring(0,350) }
                if ($Evidence.Count -lt 10) {
                    $Evidence += ("L" + [string]$LineNo + ": " + $Clean)
                }
            }
        }
    }

    $LooseHits += [pscustomobject]@{
        path = $Rel
        bytes = [long]$File.Length
        sha256 = $Sha
        strong_hits = [int]$StrongCount
        anchors = [string]::Join(",", $Anchors)
        evidence = [string]::Join(" || ", $Evidence)
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

foreach ($Archive in $ArchiveRows) {
    $ArchivePath = Join-Path $ProjectRoot ($Archive.archive.Replace("/","\"))
    $Zip = $null

    try {
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)

        foreach ($Entry in $Zip.Entries) {
            if ([string]::IsNullOrWhiteSpace($Entry.Name)) { continue }

            $EntryExt = [System.IO.Path]::GetExtension($Entry.Name).ToLowerInvariant()
            if (-not ($TextExts -contains $EntryExt)) { continue }
            if ($Entry.Length -gt 5242880) { continue }

            $EntryNameMatch = ($Entry.FullName -match $NameRx)
            $Stream = $null
            $Reader = $null
            $Text = ""

            try {
                $Stream = $Entry.Open()
                $Reader = New-Object System.IO.StreamReader($Stream, [System.Text.Encoding]::UTF8, $true)
                $Text = $Reader.ReadToEnd()
            }
            finally {
                if ($Reader -ne $null) { $Reader.Dispose() }
                elseif ($Stream -ne $null) { $Stream.Dispose() }
            }

            $EntryContentMatch = ($Text -match $ContentRx)
            if (-not ($EntryNameMatch -or $EntryContentMatch)) {
                continue
            }

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

            $Anchors = @()
            foreach ($KV in $KnownHashes.GetEnumerator()) {
                if ($EntrySha -eq $KV.Value) {
                    $Anchors += [string]$KV.Key
                    $KnownHashHits += [pscustomobject]@{
                        source = "zip"
                        anchor = [string]$KV.Key
                        sha256 = $EntrySha
                        location = ($Archive.archive + "::" + $Entry.FullName)
                    }
                }
            }

            $StrongCount = 0
            $Evidence = @()
            $LineNo = 0

            foreach ($Line in ($Text -split "\r?\n")) {
                $LineNo++
                if ($Line -match $StrongRx) {
                    $StrongCount++
                    $Clean = $Line.Trim()
                    if ($Clean.Length -gt 350) { $Clean = $Clean.Substring(0,350) }
                    if ($Evidence.Count -lt 10) {
                        $Evidence += ("L" + [string]$LineNo + ": " + $Clean)
                    }
                }
            }

            $ZipHits += [pscustomobject]@{
                archive = $Archive.archive
                entry = $Entry.FullName
                bytes = [long]$Entry.Length
                sha256 = $EntrySha
                strong_hits = [int]$StrongCount
                anchors = [string]::Join(",", $Anchors)
                evidence = [string]::Join(" || ", $Evidence)
            }
        }
    }
    catch {
        $ZipHits += [pscustomobject]@{
            archive = $Archive.archive
            entry = "__ARCHIVE_READ_ERROR__"
            bytes = 0
            sha256 = ""
            strong_hits = 0
            anchors = ""
            evidence = $_.Exception.Message
        }
    }
    finally {
        if ($Zip -ne $null) { $Zip.Dispose() }
    }
}

$LooseHits = @($LooseHits | Sort-Object @{Expression={$_.strong_hits};Descending=$true}, path)
$ZipHits = @($ZipHits | Sort-Object @{Expression={$_.strong_hits};Descending=$true}, archive, entry)

$LooseLines = @("strong_hits" + $TAB + "sha256" + $TAB + "anchors" + $TAB + "bytes" + $TAB + "path" + $TAB + "evidence")
foreach ($R in $LooseHits) {
    $Safe = ([string]$R.evidence).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $LooseLines += ([string]$R.strong_hits + $TAB + [string]$R.sha256 + $TAB + [string]$R.anchors + $TAB + [string]$R.bytes + $TAB + [string]$R.path + $TAB + $Safe)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "loose_source_hits.tsv"), ([string]::Join($LF,$LooseLines) + $LF), $Utf8)

$ZipLines = @("strong_hits" + $TAB + "sha256" + $TAB + "anchors" + $TAB + "bytes" + $TAB + "archive" + $TAB + "entry" + $TAB + "evidence")
foreach ($R in $ZipHits) {
    $Safe = ([string]$R.evidence).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $ZipLines += ([string]$R.strong_hits + $TAB + [string]$R.sha256 + $TAB + [string]$R.anchors + $TAB + [string]$R.bytes + $TAB + [string]$R.archive + $TAB + [string]$R.entry + $TAB + $Safe)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "zip_source_hits.tsv"), ([string]::Join($LF,$ZipLines) + $LF), $Utf8)

$ArchiveLines = @("sha256" + $TAB + "bytes" + $TAB + "archive")
foreach ($R in $ArchiveRows) {
    $ArchiveLines += ([string]$R.sha256 + $TAB + [string]$R.bytes + $TAB + [string]$R.archive)
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "archives.tsv"), ([string]::Join($LF,$ArchiveLines) + $LF), $Utf8)

$State = [pscustomobject]@{
    experiment = "C1.20P_STAGE3_DEEP_PROVENANCE"
    status = "READ_ONLY_SEARCH"
    stage2_freeze_sha256 = $ExpectedStage2Freeze
    loose_hits = [int]$LooseHits.Count
    zip_archives = [int]$ArchiveRows.Count
    zip_hits = [int]$ZipHits.Count
    known_hash_hits = @($KnownHashHits)
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    project_code_execution = "NONE"
    archive_extraction = "NONE"
}
[System.IO.File]::WriteAllText((Join-Path $OutDir "state.json"), (($State | ConvertTo-Json -Depth 6) + $LF), $Utf8)

$Report = @()
$Report += "# C1.20P Stage3 deep provenance search"
$Report += ""
$Report += "STATUS: READ-ONLY SEARCH"
$Report += ("Stage2 freeze: " + $ExpectedStage2Freeze)
$Report += ("Loose source hits: " + [string]$LooseHits.Count)
$Report += ("ZIP archives inspected: " + [string]$ArchiveRows.Count)
$Report += ("ZIP source hits: " + [string]$ZipHits.Count)
$Report += ("Known hash hits: " + [string]$KnownHashHits.Count)
$Report += "Training: NONE"
$Report += "Performance: NONE"
$Report += "Topology generation: NONE"
$Report += "Project-code execution: NONE"
$Report += "Archive extraction: NONE"
$Report += ""
$Report += "## Top loose hits"
$Report += ""

foreach ($R in ($LooseHits | Select-Object -First 25)) {
    $Report += ("[" + [string]$R.strong_hits + "] " + [string]$R.path + " | SHA256=" + [string]$R.sha256)
    if (-not [string]::IsNullOrWhiteSpace([string]$R.anchors)) {
        $Report += ("ANCHOR=" + [string]$R.anchors)
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$R.evidence)) {
        $Report += ([string]$R.evidence)
    }
    $Report += ""
}

$Report += "## Top ZIP hits"
$Report += ""

foreach ($R in ($ZipHits | Where-Object { $_.entry -ne "__ARCHIVE_READ_ERROR__" } | Select-Object -First 30)) {
    $Report += ("[" + [string]$R.strong_hits + "] " + [string]$R.archive + "::" + [string]$R.entry + " | SHA256=" + [string]$R.sha256)
    if (-not [string]::IsNullOrWhiteSpace([string]$R.anchors)) {
        $Report += ("ANCHOR=" + [string]$R.anchors)
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$R.evidence)) {
        $Report += ([string]$R.evidence)
    }
    $Report += ""
}

$Report += "## Decision boundary"
$Report += ""
$Report += "A surviving exact historical builder requires source-body evidence for candidate generation + eligibility + pairing/selection. A known SHA match strengthens provenance. If no such source survives, record absence and proceed only with an explicitly recovered/reconstructed builder validated against frozen C1.18 invariants."

[System.IO.File]::WriteAllText((Join-Path $OutDir "PROVENANCE_REPORT.md"), ([string]::Join($LF,$Report) + $LF), $Utf8)

$Verify = @'
param([string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage3_deep_provenance_v1")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage3_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE3_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage3_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE3_FREEZE_SHA256.txt" }

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
if ($Actual -ne $Expected) { throw "STAGE3 FREEZE MISMATCH" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "state.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }
if ($I.project_code_execution -ne "NONE") { throw "CODE EXECUTION BOUNDARY FAILURE" }
if ($I.archive_extraction -ne "NONE") { throw "ARCHIVE EXTRACTION BOUNDARY FAILURE" }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE3 PROVENANCE VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "LOOSE HITS           : $($I.loose_hits)"
Write-Host "ZIP ARCHIVES         : $($I.zip_archives)"
Write-Host "ZIP HITS             : $($I.zip_hits)"
Write-Host "KNOWN HASH HITS      : $(@($I.known_hash_hits).Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText((Join-Path $OutDir "verify_only.ps1"), ($Verify.Trim() + $LF), $Utf8)

$ManifestFiles = @(
    "PROVENANCE_REPORT.md",
    "archives.tsv",
    "loose_source_hits.tsv",
    "state.json",
    "verify_only.ps1",
    "zip_source_hits.tsv"
)
[Array]::Sort($ManifestFiles,[System.StringComparer]::Ordinal)

$ManifestLines = @()
foreach ($Rel in $ManifestFiles) {
    $Full = Join-Path $OutDir $Rel
    $Info = Get-Item -LiteralPath $Full
    $Sha = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    $ManifestLines += ($Sha + $TAB + [string]$Info.Length + $TAB + $Rel)
}

$ManifestPath = Join-Path $OutDir "stage3_manifest.tsv"
[System.IO.File]::WriteAllText($ManifestPath, ([string]::Join($LF,$ManifestLines) + $LF), $Utf8)

$Stage3Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText((Join-Path $OutDir "STAGE3_FREEZE_SHA256.txt"), ($Stage3Freeze + "  stage3_manifest.tsv" + $LF), $Utf8)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object { $_.IsReadOnly = $true }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE3 DEEP PROVENANCE FROZEN"
Write-Host "STAGE2 FREEZE SHA256 : $ExpectedStage2Freeze"
Write-Host "STAGE3 FREEZE SHA256 : $Stage3Freeze"
Write-Host "LOOSE HITS           : $($LooseHits.Count)"
Write-Host "ZIP ARCHIVES         : $($ArchiveRows.Count)"
Write-Host "ZIP HITS             : $($ZipHits.Count)"
Write-Host "KNOWN HASH HITS      : $($KnownHashHits.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("=" * 100)
