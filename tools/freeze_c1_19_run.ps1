param(
    [string]$RunDir = "C:\ABGEN\07_Resultados\Informes\c1_19r_kmnist_transport_run",
    [string]$ClosureDir = "C:\ABGEN\07_Resultados\Informes\c1_19r_kmnist_transport_closure_v1"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RunDir -PathType Container)) {
    throw "RUN DIR NOT FOUND: $RunDir"
}

if (Test-Path -LiteralPath $ClosureDir) {
    throw "CLOSURE DIR ALREADY EXISTS; refusing overwrite: $ClosureDir"
}

$completeCount = (Get-ChildItem -LiteralPath $RunDir -Filter "complete.json" -File -Recurse).Count
$modelCount = (Get-ChildItem -LiteralPath $RunDir -Filter "model.pt" -File -Recurse).Count

if ($completeCount -ne 160) {
    throw "EXPECTED 160 complete.json; FOUND $completeCount"
}
if ($modelCount -ne 160) {
    throw "EXPECTED 160 model.pt; FOUND $modelCount"
}

$files = Get-ChildItem -LiteralPath $RunDir -File -Recurse
$pathMap = @{}
[string[]]$relativePaths = @()

foreach ($file in $files) {
    $rel = $file.FullName.Substring($RunDir.Length).TrimStart("\").Replace("\","/")
    if ($pathMap.ContainsKey($rel)) {
        throw "DUPLICATE RELATIVE PATH: $rel"
    }
    $pathMap[$rel] = $file.FullName
    $relativePaths += $rel
}

[Array]::Sort($relativePaths, [System.StringComparer]::Ordinal)

$manifestLines = New-Object System.Collections.Generic.List[string]
[long]$totalBytes = 0

foreach ($rel in $relativePaths) {
    $full = $pathMap[$rel]
    $info = Get-Item -LiteralPath $full
    $sha = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $totalBytes += [long]$info.Length
    $manifestLines.Add("$sha$([char]9)$($info.Length)$([char]9)$rel")
}

New-Item -ItemType Directory -Path $ClosureDir | Out-Null

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$lf = [char]10
$manifestText = [string]::Join($lf, $manifestLines) + $lf
$manifestPath = Join-Path $ClosureDir "run_tree_manifest.tsv"
[System.IO.File]::WriteAllText($manifestPath, $manifestText, $utf8NoBom)

$treeSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()

$closure = [ordered]@{
    experiment = "C1.19R_KMNIST_TRANSPORT"
    status = "CLOSED_PASS"
    models = 160
    cells = 3200
    pair_wins_b1 = "16/16"
    t_obs = 0.002128195102507025
    p_exact = 0.0000152587890625
    upper_tail = "1/65536"
    refit = "NO"
    optional_stopping = "NO"
    run_dir = $RunDir
    file_count = $files.Count
    total_bytes = $totalBytes
    complete_json_count = $completeCount
    model_pt_count = $modelCount
    tree_manifest_sha256 = $treeSha
    c1_19p_historical_freeze_sha256 = "9ddf3004bdebcbcfc60f392285292238a8449f038965c69e02353c39e3951b54"
    c1_19d_recovery_freeze_sha256 = "551bc7fdbfd4ac3cf587bdddc6abe5e79f7963992484104ff14bba83babdd548"
    base_topology_sha256 = "74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234"
    damage_sha256 = "84e8fbf7bf545b4f81a1075e25e7c02f6156236d9f5e96313f4fa5815c657b9d"
    calibration_sha256 = "5472743a6c8bc2598aa247a14c3d345d4d971ce982b5a545a51d72f6b04f2d82"
    recovery_boundary = "C1.19R_RECOVERY_IMPLEMENTATION_V1; not claimed byte-identical to lost Dell runner; reconstructed and structurally verified before C1.19 performance."
}

$closureJson = $closure | ConvertTo-Json -Depth 6
$closureJsonPath = Join-Path $ClosureDir "closure.json"
[System.IO.File]::WriteAllText($closureJsonPath, $closureJson + $lf, $utf8NoBom)

$report = @"
# C1.19R KMNIST transport closure

STATUS: CLOSED PASS

- Models: 160
- Cells: 3200
- B1 pair wins: 16/16
- T_obs: +0.002128195102507025
- p_exact: 1.52587890625e-05
- Upper tail: 1/65536
- Refit: NO
- Optional stopping: NO
- complete.json: $completeCount
- model.pt: $modelCount
- Run-tree files: $($files.Count)
- Run-tree bytes: $totalBytes
- Run-tree manifest SHA-256: $treeSha

Recovery boundary: C1.19R_RECOVERY_IMPLEMENTATION_V1 is not claimed byte-identical to the lost Dell runner. It was reconstructed and structurally verified before C1.19 performance.

The run-tree manifest is canonical UTF-8 without BOM, sorted by ordinal relative path, with rows:
SHA256<TAB>SIZE<TAB>RELATIVE_PATH
"@
[System.IO.File]::WriteAllText((Join-Path $ClosureDir "CLOSURE_REPORT.md"), $report.Trim() + $lf, $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $ClosureDir "RUN_TREE_SHA256.txt"), $treeSha + "  run_tree_manifest.tsv" + $lf, $utf8NoBom)

Get-ChildItem -LiteralPath $RunDir -File -Recurse | ForEach-Object {
    $_.IsReadOnly = $true
}

Write-Host ("=" * 100)
Write-Host "PASS: C1.19R RUN TREE SEALED"
Write-Host "MODELS               : 160"
Write-Host "CELLS                : 3200"
Write-Host "COMPLETE.JSON        : $completeCount"
Write-Host "MODEL.PT             : $modelCount"
Write-Host "FILES                : $($files.Count)"
Write-Host "BYTES                : $totalBytes"
Write-Host "RUN TREE SHA256      : $treeSha"
Write-Host "CLOSURE DIR          : $ClosureDir"
Write-Host "RUN FILES READ-ONLY  : YES"
Write-Host ("=" * 100)
