param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage1_inventory_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage0Freeze = "5b5e58101136e6eaf050c4371f5a1226abe92d9024b32f2258c845f291d93f1e"
$Stage0Dir = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage0_preflight_v1"
$Stage0FreezeFile = Join-Path $Stage0Dir "STAGE0_FREEZE_SHA256.txt"

$KnownAnchors = @{
    "C1.17B1_SOURCE" = "732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463"
    "C1.17B2_SOURCE" = "cd6be85673b156fa08ef05281bb5cae238e5781232c66866f08a87b223dd0dda"
    "C1.17B3_RUNNER" = "0ce6dfbef2d954b5cd89690deed309c62ee82043d17fe282ceb72fbfaf2f31a0"
    "C1.17B1_SELECTION" = "21415db8372817c165306d70f6780cb33a79aa392a11f84ff52f3ff977cbbf22"
    "C1.17B1_PREDICTIONS" = "73d8466a1323f232568d4f2c724072ae57fa676c33d62fe5894963283d77d657"
    "BASE_TOPOLOGY" = "74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234"
}

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "PROJECT ROOT NOT FOUND: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $Stage0FreezeFile -PathType Leaf)) {
    throw "STAGE0 FREEZE FILE NOT FOUND: $Stage0FreezeFile"
}

$ObservedStage0 = (Get-Content -LiteralPath $Stage0FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage0 -ne $ExpectedStage0Freeze) {
    throw "STAGE0 FREEZE MISMATCH. EXPECTED $ExpectedStage0Freeze ; FOUND $ObservedStage0"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE1_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "VALID OR FROZEN STAGE1 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Write-Host "REMOVING PARTIAL UNFROZEN STAGE1 DIRECTORY: $OutDir"
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}

$Extensions = @(".py",".ps1",".json",".csv",".tsv",".md",".txt",".yaml",".yml",".toml",".ini")
$PathRx = '(?i)(c1[_\.-]?(16|17|18|19)|flycore|topolog|structur|selection|selected|pair|bank|rde)'
$ContentRx = '(?i)(950100|1810000|1820000|C1\.17B1|C1\.18|selected[_ -]?topolog|topolog(y|ies)|structural[_ -]?bank|pairing|eligib|delta[_ -]?RDE|74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234)'
$ExcludeRx = '(?i)(\\\.venv\\|\\__pycache__\\|\\c1_19r_kmnist_transport_run\\|\\c1_20p_stage0_preflight_v1\\|\\c1_20p_stage1_inventory_v1\\|\\04_Codigo\\tools\\c1_20_)'

$Files = @(
    Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse |
    Where-Object {
        ($Extensions -contains $_.Extension.ToLowerInvariant()) -and
        ($_.FullName -notmatch $ExcludeRx)
    }
)

$CandidateRows = @()
$ContentMatchRows = @()
$AnchorHitRows = @()

foreach ($File in $Files) {
    $Rel = $File.FullName.Substring($ProjectRoot.Length).TrimStart("\").Replace("\","/")
    $PathMatch = ($Rel -match $PathRx)
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

    if (-not ($PathMatch -or $ContentMatch)) {
        continue
    }

    $Sha = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $Score = 0

    if ($File.Extension -ieq ".py") { $Score += 3 }
    if ($Rel -match '(?i)c1[_\.-]?18') { $Score += 7 }
    if ($Rel -match '(?i)c1[_\.-]?17') { $Score += 5 }
    if ($Rel -match '(?i)topolog|structur') { $Score += 4 }
    if ($Rel -match '(?i)selection|selected|pair|bank') { $Score += 3 }
    if ($Text -match '1820000') { $Score += 10 }
    if ($Text -match '1810000') { $Score += 7 }
    if ($Text -match '950100') { $Score += 7 }
    if ($Text -match '(?i)eligib|pairing') { $Score += 4 }
    if ($Text -match '(?i)delta[_ -]?RDE') { $Score += 4 }
    if ($Text -match '74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234') { $Score += 8 }

    $AnchorNames = @()
    foreach ($KV in $KnownAnchors.GetEnumerator()) {
        if ($Sha -eq $KV.Value) {
            $AnchorNames += [string]$KV.Key
            $AnchorHitRows += [pscustomobject]@{
                anchor = [string]$KV.Key
                sha256 = $Sha
                path = $Rel
            }
            $Score += 20
        }
    }

    $Kind = "manifest_or_record"
    if (($File.Extension -ieq ".py") -or ($File.Extension -ieq ".ps1")) {
        $Kind = "source"
    }

    $CandidateRows += [pscustomobject]@{
        score = [int]$Score
        kind = $Kind
        path = $Rel
        bytes = [long]$File.Length
        sha256 = $Sha
        anchors = [string]::Join(",", $AnchorNames)
    }

    if (-not [string]::IsNullOrEmpty($Text)) {
        $LineNo = 0
        $Found = 0
        foreach ($Line in ($Text -split "\r?\n")) {
            $LineNo++
            if ($Line -match $ContentRx) {
                $Clean = $Line.Trim()
                if ($Clean.Length -gt 400) {
                    $Clean = $Clean.Substring(0,400)
                }
                $ContentMatchRows += [pscustomobject]@{
                    path = $Rel
                    line = [int]$LineNo
                    text = $Clean
                }
                $Found++
                if ($Found -ge 6) {
                    break
                }
            }
        }
    }
}

$Sorted = @(
    $CandidateRows |
    Sort-Object -Property @{Expression={$_.score};Descending=$true}, @{Expression={$_.path};Descending=$false}
)
$Top = @($Sorted | Select-Object -First 40)

New-Item -ItemType Directory -Path $OutDir | Out-Null

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$Inventory = [pscustomobject]@{
    experiment = "C1.20P_STAGE1_LOCAL_INVENTORY"
    status = "INVENTORY_ONLY"
    stage0_freeze_sha256 = $ExpectedStage0Freeze
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    text_files_scanned = [int]$Files.Count
    candidate_files = [int]$Sorted.Count
    known_anchor_hits = @($AnchorHitRows)
    candidates = @($Sorted)
}

$InventoryJson = $Inventory | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "inventory.json"),
    ($InventoryJson + $LF),
    $Utf8
)

$Lines = @()
$Lines += ("score" + $TAB + "kind" + $TAB + "sha256" + $TAB + "bytes" + $TAB + "anchors" + $TAB + "path")
foreach ($C in $Sorted) {
    $Lines += (
        [string]$C.score + $TAB +
        [string]$C.kind + $TAB +
        [string]$C.sha256 + $TAB +
        [string]$C.bytes + $TAB +
        [string]$C.anchors + $TAB +
        [string]$C.path
    )
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "inventory.tsv"),
    ([string]::Join($LF,$Lines) + $LF),
    $Utf8
)

$MatchLines = @()
$MatchLines += ("path" + $TAB + "line" + $TAB + "text")
foreach ($M in $ContentMatchRows) {
    $Safe = ([string]$M.text).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $MatchLines += ([string]$M.path + $TAB + [string]$M.line + $TAB + $Safe)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "content_matches.tsv"),
    ([string]::Join($LF,$MatchLines) + $LF),
    $Utf8
)

$TopLines = @()
$TopLines += "# C1.20 Stage1 top candidates"
$TopLines += ""
$TopLines += "INVENTORY ONLY -- NO TRAINING -- NO PERFORMANCE -- NO TOPOLOGY GENERATION"
$TopLines += ("Stage0 freeze: " + $ExpectedStage0Freeze)
$TopLines += ""
foreach ($C in $Top) {
    $A = [string]$C.anchors
    if ([string]::IsNullOrWhiteSpace($A)) {
        $A = "-"
    }
    $TopLines += ("SCORE=" + [string]$C.score + " | " + [string]$C.kind + " | SHA256=" + [string]$C.sha256)
    $TopLines += ("PATH=" + [string]$C.path)
    $TopLines += ("ANCHORS=" + $A)
    $TopLines += ""
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "TOP_CANDIDATES.md"),
    ([string]::Join($LF,$TopLines) + $LF),
    $Utf8
)

$SummaryLines = @()
$SummaryLines += "# C1.20P Stage1 local inventory"
$SummaryLines += ""
$SummaryLines += "- Status: INVENTORY ONLY"
$SummaryLines += ("- Stage0 freeze SHA-256: " + $ExpectedStage0Freeze)
$SummaryLines += ("- Text files scanned: " + [string]$Files.Count)
$SummaryLines += ("- Candidate files: " + [string]$Sorted.Count)
$SummaryLines += ("- Known hash-anchor hits: " + [string]$AnchorHitRows.Count)
$SummaryLines += "- Training: NONE"
$SummaryLines += "- Performance: NONE"
$SummaryLines += "- Topology generation: NONE"
$SummaryLines += ""
$SummaryLines += "Next: identify and lock the exact structural builder and prior selected-topology manifests before any C1.20 candidate generation."

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "SUMMARY.md"),
    ([string]::Join($LF,$SummaryLines) + $LF),
    $Utf8
)

$Verify = @'
param(
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage1_inventory_v1"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage1_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE1_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage1_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE1_FREEZE_SHA256.txt" }

$Expected = (Get-Content -LiteralPath $Freeze -Raw).Trim().Split()[0].ToLowerInvariant()
$ManifestRows = @(Get-Content -LiteralPath $Manifest)

foreach ($Row in $ManifestRows) {
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
if ($Actual -ne $Expected) { throw "STAGE1 FREEZE MISMATCH. EXPECTED $Expected ; FOUND $Actual" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "inventory.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }

$AnchorCount = @($I.known_anchor_hits).Count

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE1 INVENTORY VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "TEXT FILES SCANNED   : $($I.text_files_scanned)"
Write-Host "CANDIDATE FILES      : $($I.candidate_files)"
Write-Host "KNOWN ANCHOR HITS    : $AnchorCount"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "verify_only.ps1"),
    ($Verify.Trim() + $LF),
    $Utf8
)

$ManifestFiles = @(
    "SUMMARY.md",
    "TOP_CANDIDATES.md",
    "content_matches.tsv",
    "inventory.json",
    "inventory.tsv",
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

$ManifestPath = Join-Path $OutDir "stage1_manifest.tsv"
[System.IO.File]::WriteAllText(
    $ManifestPath,
    ([string]::Join($LF,$ManifestLines) + $LF),
    $Utf8
)

$Stage1Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "STAGE1_FREEZE_SHA256.txt"),
    ($Stage1Freeze + "  stage1_manifest.tsv" + $LF),
    $Utf8
)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object {
    $_.IsReadOnly = $true
}

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE1 LOCAL INVENTORY FROZEN"
Write-Host "STAGE0 FREEZE SHA256 : $ExpectedStage0Freeze"
Write-Host "TEXT FILES SCANNED   : $($Files.Count)"
Write-Host "CANDIDATE FILES      : $($Sorted.Count)"
Write-Host "KNOWN ANCHOR HITS    : $($AnchorHitRows.Count)"
Write-Host "STAGE1 FREEZE SHA256 : $Stage1Freeze"
Write-Host "OUT DIR              : $OutDir"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host ("-" * 100)
Write-Host "TOP CANDIDATES:"

foreach ($C in ($Top | Select-Object -First 15)) {
    $AnchorText = ""
    if (-not [string]::IsNullOrWhiteSpace([string]$C.anchors)) {
        $AnchorText = " ANCHOR=" + [string]$C.anchors
    }
    Write-Host ("[" + [string]$C.score + "] " + [string]$C.sha256 + "  " + [string]$C.path + $AnchorText)
}

Write-Host ("=" * 100)
