param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage11a_replay_impl_audit_v1"
)

$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

$S10="0853fc59b137b98b78d489bd95996c7040ae4509c2c5c46525d6119b43b7574f"
$S10File=Join-Path $Root "07_Resultados\Informes\c1_20p_stage10_selection_spec_v1\STAGE10_FREEZE_SHA256.txt"

$C118=Join-Path $Root "00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\c1_18a_runner.py"
$C119=Join-Path $Root "04_Codigo\training\c1_19r_recovery\c1_19r_recovery_runner.py"

$ExpectedC118="19cb9848792373cc2612a4e494268e0e6c71bf4dc7d2ce1c292f2a1fa5758a28"
$ExpectedC119="5522b3cc5a49aec7bd53282f1a54b2bc97f0194f9221124fbe7f664290d41929"

if(-not(Test-Path $S10File)){throw "STAGE10 FREEZE FILE MISSING"}
if((Get-Content $S10File -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S10){throw "STAGE10 FREEZE MISMATCH"}

foreach($x in @(
  [pscustomobject]@{p=$C118;h=$ExpectedC118;n="c1_18a_runner.py"},
  [pscustomobject]@{p=$C119;h=$ExpectedC119;n="c1_19r_recovery_runner.py"}
)){
  if(-not(Test-Path $x.p)){throw "MISSING $($x.n)"}
  $h=(Get-FileHash $x.p -Algorithm SHA256).Hash.ToLowerInvariant()
  if($h -ne $x.h){throw "SHA MISMATCH $($x.n)"}
}

if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE11A_FREEZE_SHA256.txt")){throw "FROZEN STAGE11A EXISTS"}
  Remove-Item $Out -Recurse -Force
}
New-Item -ItemType Directory -Path $Out|Out-Null

$u=New-Object System.Text.UTF8Encoding($false)
$lf=[char]10
$tab=[char]9

function Window-Lines {
  param([string]$Path,[int]$Start,[int]$End)
  $lines=@(Get-Content -LiteralPath $Path)
  $o=@()
  for($n=$Start;$n -le $End;$n++){
    if($n -le $lines.Count){$o+=("L"+[string]$n+": "+[string]$lines[$n-1])}
  }
  return $o
}

$c118Text=[string](Get-Content $C118 -Raw)
$c119Text=[string](Get-Content $C119 -Raw)

$runnerWindows=@()
$runnerWindows+="===== c1_18a_runner.py IMPORTS / CONSTANTS L1-L80 ====="
$runnerWindows+=@(Window-Lines $C118 1 80)
$runnerWindows+=""
$runnerWindows+="===== c1_18a_runner.py RECONSTRUCT_VARIANTS L176-L234 ====="
$runnerWindows+=@(Window-Lines $C118 176 234)
$runnerWindows+=""
$runnerWindows+="===== c1_19r_recovery_runner.py TOPOLOGY PRIMITIVES L60-L171 ====="
$runnerWindows+=@(Window-Lines $C119 60 171)
$runnerWindows+=""
$runnerWindows+="===== c1_19r_recovery_runner.py RECONSTRUCT_VARIANTS L374-L405 ====="
$runnerWindows+=@(Window-Lines $C119 374 405)
$runnerWindows+=""
[IO.File]::WriteAllText((Join-Path $Out "RUNNER_WINDOWS.txt"),([string]::Join($lf,$runnerWindows)+$lf),$u)

$aliasLines=@("file"+$tab+"line"+$tab+"text")
foreach($pair in @(
  [pscustomobject]@{p=$C118;n="c1_18a_runner.py"},
  [pscustomobject]@{p=$C119;n="c1_19r_recovery_runner.py"}
)){
  $lines=@(Get-Content $pair.p)
  for($i=0;$i -lt $lines.Count;$i++){
    $z=[string]$lines[$i]
    if($z -match '(?i)(^\s*import\s+|^\s*from\s+|a5b|metrics_for|summary_row|reconstruct_variants|build_flycore_c0_topology|edge_hash)'){
      $aliasLines+=($pair.n+$tab+[string]($i+1)+$tab+$z.Trim())
    }
  }
}
[IO.File]::WriteAllText((Join-Path $Out "RUNNER_IMPORT_AND_API_LINES.tsv"),([string]::Join($lf,$aliasLines)+$lf),$u)

$CodeRoot=Join-Path $Root "04_Codigo"
$Py=@(
  Get-ChildItem -LiteralPath $CodeRoot -File -Recurse -Filter *.py -ErrorAction SilentlyContinue |
  Where-Object {$_.FullName -notmatch '(?i)\\\.venv\\|\\__pycache__\\'}
)

$candidates=@()
foreach($f in $Py){
  if($f.Length -gt 5242880){continue}
  $txt=""
  try{$txt=[string](Get-Content $f.FullName -Raw)}catch{continue}
  $hasMetrics=($txt -match '(?m)^\s*def\s+metrics_for\s*\(')
  $hasSummary=($txt -match '(?m)^\s*def\s+summary_row\s*\(')
  if($hasMetrics -or $hasSummary){
    $rel=$f.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")
    $sha=(Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $candidates+=[pscustomobject]@{
      path=$rel;full=$f.FullName;sha256=$sha;bytes=[long]$f.Length;
      has_metrics_for=$hasMetrics;has_summary_row=$hasSummary
    }
  }
}

$srcLines=@("sha256"+$tab+"bytes"+$tab+"metrics_for"+$tab+"summary_row"+$tab+"path")
foreach($c in ($candidates|Sort-Object path)){
  $srcLines+=($c.sha256+$tab+[string]$c.bytes+$tab+[string]$c.has_metrics_for+$tab+[string]$c.has_summary_row+$tab+$c.path)
}
[IO.File]::WriteAllText((Join-Path $Out "METRICS_SOURCE_CANDIDATES.tsv"),([string]::Join($lf,$srcLines)+$lf),$u)

$metricWindows=@()
foreach($c in ($candidates|Sort-Object path)){
  $lines=@(Get-Content $c.full)
  $metricWindows+=("===== "+$c.path+" SHA256="+$c.sha256+" =====")
  for($i=0;$i -lt $lines.Count;$i++){
    $z=[string]$lines[$i]
    if($z -match '^\s*def\s+(metrics_for|summary_row)\s*\('){
      $a=[Math]::Max(1,$i+1-8)
      $b=[Math]::Min($lines.Count,$i+1+90)
      $metricWindows+=@(Window-Lines $c.full $a $b)
      $metricWindows+=""
    }
  }
}
[IO.File]::WriteAllText((Join-Path $Out "METRICS_SOURCE_WINDOWS.txt"),([string]::Join($lf,$metricWindows)+$lf),$u)

$both=@($candidates|Where-Object{$_.has_metrics_for -and $_.has_summary_row})
$state=[pscustomobject]@{
  status="READ_ONLY_REPLAY_IMPLEMENTATION_AUDIT"
  stage10_freeze_sha256=$S10
  c1_18a_runner_sha256=$ExpectedC118
  c1_19r_recovery_runner_sha256=$ExpectedC119
  python_files_scanned=[int]$Py.Count
  metrics_source_candidates=[int]$candidates.Count
  sources_with_both_metrics_for_and_summary_row=[int]$both.Count
  training="NONE"
  performance="NONE"
  topology_generation="NONE"
  project_code_execution="NONE"
}
[IO.File]::WriteAllText((Join-Path $Out "state.json"),(($state|ConvertTo-Json -Depth 5)+$lf),$u)

$report=@(
  "# C1.20P Stage11A replay implementation audit",
  "",
  "STATUS: READ-ONLY IMPLEMENTATION AUDIT",
  "Stage10 freeze: "+$S10,
  "c1_18a_runner SHA256: "+$ExpectedC118,
  "c1_19r_recovery_runner SHA256: "+$ExpectedC119,
  "Python files scanned: "+[string]$Py.Count,
  "Metrics source candidates: "+[string]$candidates.Count,
  "Sources containing BOTH metrics_for and summary_row: "+[string]$both.Count,
  "Training: NONE",
  "Performance: NONE",
  "Topology generation: NONE",
  "Project-code execution: NONE",
  "",
  "## Decision boundary",
  "",
  "Stage11B replay is authorized only after the exact source dependency used for structural metrics is identified and hash-bound. If multiple incompatible candidates remain, do not execute replay until resolved."
)
[IO.File]::WriteAllText((Join-Path $Out "REPORT.md"),([string]::Join($lf,$report)+$lf),$u)

$files=@("METRICS_SOURCE_CANDIDATES.tsv","METRICS_SOURCE_WINDOWS.txt","REPORT.md","RUNNER_IMPORT_AND_API_LINES.tsv","RUNNER_WINDOWS.txt","state.json")
$m=@()
foreach($f in $files){
  $p=Join-Path $Out $f;$i=Get-Item $p;$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  $m+=($h+$tab+[string]$i.Length+$tab+$f)
}
[IO.File]::WriteAllText((Join-Path $Out "stage11a_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)
$freeze=(Get-FileHash (Join-Path $Out "stage11a_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE11A_FREEZE_SHA256.txt"),($freeze+"  stage11a_manifest.tsv"+$lf),$u)
Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}

Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE11A REPLAY IMPLEMENTATION AUDIT FROZEN"
Write-Host "STAGE10 FREEZE SHA256 : $S10"
Write-Host "STAGE11A FREEZE SHA256: $freeze"
Write-Host "PY FILES SCANNED      : $($Py.Count)"
Write-Host "METRICS CANDIDATES    : $($candidates.Count)"
Write-Host "BOTH API FUNCTIONS    : $($both.Count)"
Write-Host "TRAINING              : NONE"
Write-Host "PERFORMANCE           : NONE"
Write-Host "TOPOLOGY GENERATION   : NONE"
Write-Host "PROJECT CODE EXEC     : NONE"
Write-Host ("="*100)
