param(
    [string]$ProjectRoot = "C:\ABGEN",
    [string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage4_zip_builder_audit_v1"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedStage3Freeze = "54f9c3439be006a03643453afdc40ec18dce96c283763e989b4dc2f51e4f8bff"
$Stage3FreezeFile = Join-Path $ProjectRoot "07_Resultados\Informes\c1_20p_stage3_deep_provenance_v1\STAGE3_FREEZE_SHA256.txt"
$ArchiveRel = "00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\c1_18p_stage0_v1.zip"
$ArchivePath = Join-Path $ProjectRoot $ArchiveRel

$ExpectedEntries = @(
    [pscustomobject]@{ name="c1_18p_derive_dev_builder.py"; sha="d47fe09e3e23cdad4cf047ed4ccb2945cba3fd81e9fb32630ea0cfe00ac0db4f" },
    [pscustomobject]@{ name="c1_18p_spec.py"; sha="fcfd0a4809374c634891f5a3e0e1a085c63533b4e56f0a0679c6cfe8015695d3" },
    [pscustomobject]@{ name="c1_18p_verify_derived_builder.py"; sha="1bb0857c1ff4ebe3315dfde62a187ee86bee55a22fe83699214e413ee76e13c8" },
    [pscustomobject]@{ name="c1_18p_source_probe.py"; sha="65945e31916e517d24238cf7798911d3379c4d3256174fc908e16e0ad3f68fd8" },
    [pscustomobject]@{ name="c1_18p_preflight.py"; sha="a8c2d3d0c500b4a96dbdff6565fb80d0863ed67c4934c83e17025ffc1e8e78e2" },
    [pscustomobject]@{ name="c1_18p_selftest.py"; sha="1ac7154ac8ed0e013b8be81e4c33815a894be6fb841cebd7c3a5dcbdfcf2e9d5" }
)

if (-not (Test-Path -LiteralPath $Stage3FreezeFile -PathType Leaf)) {
    throw "STAGE3 FREEZE FILE NOT FOUND: $Stage3FreezeFile"
}
$ObservedStage3 = (Get-Content -LiteralPath $Stage3FreezeFile -Raw).Trim().Split()[0].ToLowerInvariant()
if ($ObservedStage3 -ne $ExpectedStage3Freeze) {
    throw "STAGE3 FREEZE MISMATCH. EXPECTED $ExpectedStage3Freeze ; FOUND $ObservedStage3"
}
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "ARCHIVE NOT FOUND: $ArchivePath"
}

if (Test-Path -LiteralPath $OutDir) {
    $ExistingFreeze = Join-Path $OutDir "STAGE4_FREEZE_SHA256.txt"
    if (Test-Path -LiteralPath $ExistingFreeze -PathType Leaf) {
        throw "FROZEN STAGE4 OUTPUT ALREADY EXISTS; refusing overwrite: $OutDir"
    }
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutDir | Out-Null

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$LF = [char]10
$TAB = [char]9

$ArchiveSha = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)

$EntryRows = @()
$Texts = @{}

try {
    foreach ($Expected in $ExpectedEntries) {
        $MatchesFound = @($Zip.Entries | Where-Object { $_.FullName -eq $Expected.name })
        if ($MatchesFound.Count -ne 1) {
            throw "ENTRY COUNT MISMATCH FOR $($Expected.name): $($MatchesFound.Count)"
        }

        $Entry = $MatchesFound[0]

        $HashStream = $null
        $ShaObj = $null
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

        if ($EntrySha -ne $Expected.sha) {
            throw "ENTRY SHA MISMATCH: $($Expected.name). EXPECTED $($Expected.sha) ; FOUND $EntrySha"
        }

        $ReadStream = $null
        $Reader = $null
        try {
            $ReadStream = $Entry.Open()
            $Reader = New-Object System.IO.StreamReader($ReadStream, [System.Text.Encoding]::UTF8, $true)
            $Text = $Reader.ReadToEnd()
        }
        finally {
            if ($Reader -ne $null) { $Reader.Dispose() }
            elseif ($ReadStream -ne $null) { $ReadStream.Dispose() }
        }

        $Texts[$Expected.name] = $Text
        $EntryRows += [pscustomobject]@{
            name = $Expected.name
            sha256 = $EntrySha
            bytes = [long]$Entry.Length
        }
    }
}
finally {
    $Zip.Dispose()
}

$Categories = @(
    [pscustomobject]@{ name="PROVENANCE"; rx='(?i)(historical|derived|derive|recover|reconstruct|source|builder|stage0|preflight|freeze|lock|C1\.18|B1)' },
    [pscustomobject]@{ name="GENERATION"; rx='(?i)(candidate|seed|build|generate|topolog|edge|rng|random|mask)' },
    [pscustomobject]@{ name="ELIGIBILITY"; rx='(?i)(eligible|eligibility|filter|threshold|MIN_DELTA_RDE|delta_rde)' },
    [pscustomobject]@{ name="PAIRING_SELECTION"; rx='(?i)(pair|low|high|sort|rank|select|selected)' }
)

$ContextRows = @()
$DeclRows = @()

foreach ($EntryRow in $EntryRows) {
    $Name = [string]$EntryRow.name
    $Lines = @(([string]$Texts[$Name]) -split "\r?\n")

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $Line = [string]$Lines[$i]
        $LineNumber = $i + 1

        if ($Line -match '^\s*(def|class)\s+[A-Za-z_][A-Za-z0-9_]*') {
            $DeclRows += [pscustomobject]@{
                entry = $Name
                line = [int]$LineNumber
                declaration = $Line.Trim()
            }
        }

        foreach ($Category in $Categories) {
            if ($Line -match $Category.rx) {
                $Start = [Math]::Max(0, $i - 2)
                $End = [Math]::Min($Lines.Count - 1, $i + 2)
                $Ctx = @()

                for ($j = $Start; $j -le $End; $j++) {
                    $CtxLine = ([string]$Lines[$j]).Trim()
                    if ($CtxLine.Length -gt 420) { $CtxLine = $CtxLine.Substring(0,420) }
                    $Ctx += ("L" + [string]($j + 1) + ": " + $CtxLine)
                }

                $ContextRows += [pscustomobject]@{
                    entry = $Name
                    category = [string]$Category.name
                    line = [int]$LineNumber
                    context = [string]::Join(" || ", $Ctx)
                }
            }
        }
    }
}

$ManifestObject = [pscustomobject]@{
    experiment = "C1.20P_STAGE4_ZIP_BUILDER_AUDIT"
    status = "READ_ONLY_SOURCE_AUDIT"
    stage3_freeze_sha256 = $ExpectedStage3Freeze
    archive_path = $ArchiveRel.Replace("\","/")
    archive_sha256 = $ArchiveSha
    entries = @($EntryRows)
    training = "NONE"
    performance = "NONE"
    topology_generation = "NONE"
    project_code_execution = "NONE"
    executable_extraction = "NONE"
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "entry_manifest.json"),
    (($ManifestObject | ConvertTo-Json -Depth 6) + $LF),
    $Utf8
)

$DeclLines = @("entry" + $TAB + "line" + $TAB + "declaration")
foreach ($R in ($DeclRows | Sort-Object entry,line)) {
    $DeclLines += ([string]$R.entry + $TAB + [string]$R.line + $TAB + [string]$R.declaration)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "python_declarations.tsv"),
    ([string]::Join($LF,$DeclLines) + $LF),
    $Utf8
)

$ContextLines = @("entry" + $TAB + "category" + $TAB + "line" + $TAB + "context")
foreach ($R in ($ContextRows | Sort-Object entry,category,line)) {
    $Safe = ([string]$R.context).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
    $ContextLines += ([string]$R.entry + $TAB + [string]$R.category + $TAB + [string]$R.line + $TAB + $Safe)
}
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "source_context.tsv"),
    ([string]::Join($LF,$ContextLines) + $LF),
    $Utf8
)

$Report = @()
$Report += "# C1.20P Stage4 ZIP builder source audit"
$Report += ""
$Report += "STATUS: READ-ONLY SOURCE AUDIT"
$Report += ("Stage3 freeze: " + $ExpectedStage3Freeze)
$Report += ("Archive SHA256: " + $ArchiveSha)
$Report += "Training: NONE"
$Report += "Performance: NONE"
$Report += "Topology generation: NONE"
$Report += "Project-code execution: NONE"
$Report += "Executable extraction: NONE"
$Report += ""
$Report += "## Entry hashes"
$Report += ""

foreach ($R in $EntryRows) {
    $Report += ("- " + [string]$R.name + " | SHA256=" + [string]$R.sha256 + " | bytes=" + [string]$R.bytes)
}

$Report += ""
$Report += "## Python declarations"
$Report += ""

foreach ($R in ($DeclRows | Sort-Object entry,line)) {
    $Report += ("[" + [string]$R.entry + ":" + [string]$R.line + "] " + [string]$R.declaration)
}

$Report += ""
$Report += "## Structural/provenance contexts"
$Report += ""

$ImportantRows = @(
    $ContextRows |
    Where-Object {
        $_.entry -eq "c1_18p_derive_dev_builder.py" -or
        $_.entry -eq "c1_18p_spec.py" -or
        $_.entry -eq "c1_18p_verify_derived_builder.py" -or
        $_.entry -eq "c1_18p_source_probe.py"
    } |
    Sort-Object entry,category,line
)

foreach ($R in $ImportantRows) {
    $Report += ("[" + [string]$R.entry + ":" + [string]$R.category + ":" + [string]$R.line + "] " + [string]$R.context)
}

$Report += ""
$Report += "## Decision boundary"
$Report += ""
$Report += "Stage4 maps source-body evidence only. Exact historical-builder status requires provenance statements and implementation coverage for generation + eligibility + pairing/selection. If the package identifies itself as derived/reconstructed, retain that label even if it reproduces frozen historical invariants."

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "BUILDER_AUDIT_REPORT.md"),
    ([string]::Join($LF,$Report) + $LF),
    $Utf8
)

$Verify = @'
param([string]$OutDir = "C:\ABGEN\07_Resultados\Informes\c1_20p_stage4_zip_builder_audit_v1")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Manifest = Join-Path $OutDir "stage4_manifest.tsv"
$Freeze = Join-Path $OutDir "STAGE4_FREEZE_SHA256.txt"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "MISSING stage4_manifest.tsv" }
if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "MISSING STAGE4_FREEZE_SHA256.txt" }

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
if ($Actual -ne $Expected) { throw "STAGE4 FREEZE MISMATCH" }

$I = Get-Content -LiteralPath (Join-Path $OutDir "entry_manifest.json") -Raw | ConvertFrom-Json
if ($I.training -ne "NONE") { throw "TRAINING BOUNDARY FAILURE" }
if ($I.performance -ne "NONE") { throw "PERFORMANCE BOUNDARY FAILURE" }
if ($I.topology_generation -ne "NONE") { throw "TOPOLOGY BOUNDARY FAILURE" }
if ($I.project_code_execution -ne "NONE") { throw "CODE EXECUTION BOUNDARY FAILURE" }
if ($I.executable_extraction -ne "NONE") { throw "EXTRACTION BOUNDARY FAILURE" }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE4 ZIP BUILDER AUDIT VERIFY-ONLY"
Write-Host "FREEZE SHA256        : $Actual"
Write-Host "ARCHIVE SHA256       : $($I.archive_sha256)"
Write-Host "ENTRIES              : $(@($I.entries).Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "EXECUTABLE EXTRACTION: NONE"
Write-Host ("=" * 100)
'@

[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "verify_only.ps1"),
    ($Verify.Trim() + $LF),
    $Utf8
)

$ManifestFiles = @(
    "BUILDER_AUDIT_REPORT.md",
    "entry_manifest.json",
    "python_declarations.tsv",
    "source_context.tsv",
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

$ManifestPath = Join-Path $OutDir "stage4_manifest.tsv"
[System.IO.File]::WriteAllText(
    $ManifestPath,
    ([string]::Join($LF,$ManifestLines) + $LF),
    $Utf8
)

$Stage4Freeze = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText(
    (Join-Path $OutDir "STAGE4_FREEZE_SHA256.txt"),
    ($Stage4Freeze + "  stage4_manifest.tsv" + $LF),
    $Utf8
)

Get-ChildItem -LiteralPath $OutDir -File | ForEach-Object { $_.IsReadOnly = $true }

Write-Host ("=" * 100)
Write-Host "PASS: C1.20P STAGE4 ZIP BUILDER AUDIT FROZEN"
Write-Host "STAGE3 FREEZE SHA256 : $ExpectedStage3Freeze"
Write-Host "STAGE4 FREEZE SHA256 : $Stage4Freeze"
Write-Host "ARCHIVE SHA256       : $ArchiveSha"
Write-Host "ENTRIES              : $($EntryRows.Count)"
Write-Host "DECLARATIONS         : $($DeclRows.Count)"
Write-Host "CONTEXT ROWS         : $($ContextRows.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "EXECUTABLE EXTRACTION: NONE"
Write-Host ("=" * 100)
