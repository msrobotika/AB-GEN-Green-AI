param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage11a2_global_dependency_hunt_v1"
)

$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

$S11A="083260b536b3303be3f960b942ff2790a22e41fa88ddbf6d95d5e6f100dd1126"
$S11AFile=Join-Path $Root "07_Resultados\Informes\c1_20p_stage11a_replay_impl_audit_v1\STAGE11A_FREEZE_SHA256.txt"

if(-not(Test-Path $S11AFile)){throw "STAGE11A FREEZE FILE MISSING"}
if((Get-Content $S11AFile -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S11A){throw "STAGE11A FREEZE MISMATCH"}

if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE11A2_FREEZE_SHA256.txt")){throw "FROZEN STAGE11A2 EXISTS"}
  Remove-Item $Out -Recurse -Force
}
New-Item -ItemType Directory -Path $Out|Out-Null

$u=New-Object System.Text.UTF8Encoding($false)
$lf=[char]10
$tab=[char]9
$exclude='(?i)(\\\.venv\\|\\__pycache__\\|\\c1_20p_stage11a2_global_dependency_hunt_v1\\)'

$py=@(
  Get-ChildItem -LiteralPath $Root -File -Recurse -Force -Filter *.py -ErrorAction SilentlyContinue |
  Where-Object {$_.FullName -notmatch $exclude}
)

$sourceRows=@()
$refRows=@()

foreach($f in $py){
  if($f.Length -gt 10485760){continue}
  $txt=""
  try{$txt=[string](Get-Content -LiteralPath $f.FullName -Raw)}catch{continue}
  $rel=$f.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")
  $sha=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $isCommon=($f.Name -ieq "c1_16_common.py")
  $isC116=($f.Name -like "c1_16*.py")
  $hasMetrics=($txt -match '(?m)^\s*def\s+metrics_for\s*\(')
  $hasSummary=($txt -match '(?m)^\s*def\s+summary_row\s*\(')
  $hasA5b=($txt -match '(?i)\ba5b\b')
  $hasImportCommon=($txt -match '(?im)^\s*(from\s+c1_16_common|import\s+c1_16_common)\b')

  if($isCommon -or $isC116 -or $hasMetrics -or $hasSummary -or $hasA5b -or $hasImportCommon){
    $sourceRows+=[pscustomobject]@{
      source="loose";path=$rel;sha256=$sha;bytes=[long]$f.Length;
      c1_16_common=$isCommon;c1_16_file=$isC116;metrics_for=$hasMetrics;summary_row=$hasSummary;a5b_ref=$hasA5b;imports_c1_16_common=$hasImportCommon
    }
  }

  $lines=@($txt -split "\r?\n")
  for($i=0;$i -lt $lines.Count;$i++){
    $z=[string]$lines[$i]
    if($z -match '(?i)(c1_16_common|def\s+metrics_for\s*\(|def\s+summary_row\s*\(|\ba5b\b)'){
      $refRows+=[pscustomobject]@{
        source="loose";path=$rel;line=$i+1;text=$z.Trim()
      }
    }
  }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zips=@(
  Get-ChildItem -LiteralPath $Root -File -Recurse -Force -Filter *.zip -ErrorAction SilentlyContinue |
  Where-Object {$_.FullName -notmatch $exclude}
)

$zipEntryRows=@()
foreach($zf in $zips){
  $zip=$null
  try{
    $zip=[System.IO.Compression.ZipFile]::OpenRead($zf.FullName)
    foreach($e in $zip.Entries){
      if([string]::IsNullOrWhiteSpace($e.Name)){continue}
      if([IO.Path]::GetExtension($e.Name) -ine ".py"){continue}
      if($e.Length -gt 10485760){continue}

      $rs=$null;$rd=$null;$txt=""
      try{
        $rs=$e.Open()
        $rd=New-Object IO.StreamReader($rs,[Text.Encoding]::UTF8,$true)
        $txt=$rd.ReadToEnd()
      }finally{
        if($rd -ne $null){$rd.Dispose()}elseif($rs -ne $null){$rs.Dispose()}
      }

      $isCommon=([IO.Path]::GetFileName($e.FullName) -ieq "c1_16_common.py")
      $isC116=([IO.Path]::GetFileName($e.FullName) -like "c1_16*.py")
      $hasMetrics=($txt -match '(?m)^\s*def\s+metrics_for\s*\(')
      $hasSummary=($txt -match '(?m)^\s*def\s+summary_row\s*\(')
      $hasA5b=($txt -match '(?i)\ba5b\b')
      $hasImportCommon=($txt -match '(?im)^\s*(from\s+c1_16_common|import\s+c1_16_common)\b')

      if(-not($isCommon -or $isC116 -or $hasMetrics -or $hasSummary -or $hasA5b -or $hasImportCommon)){continue}

      $hs=$null;$shaObj=$null
      try{
        $hs=$e.Open()
        $shaObj=[Security.Cryptography.SHA256]::Create()
        $hb=$shaObj.ComputeHash($hs)
        $sha=([BitConverter]::ToString($hb)).Replace("-","").ToLowerInvariant()
      }finally{
        if($shaObj -ne $null){$shaObj.Dispose()}
        if($hs -ne $null){$hs.Dispose()}
      }

      $loc=$zf.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")+"::"+$e.FullName
      $zipEntryRows+=[pscustomobject]@{
        source="zip";path=$loc;sha256=$sha;bytes=[long]$e.Length;
        c1_16_common=$isCommon;c1_16_file=$isC116;metrics_for=$hasMetrics;summary_row=$hasSummary;a5b_ref=$hasA5b;imports_c1_16_common=$hasImportCommon
      }

      $lines=@($txt -split "\r?\n")
      for($i=0;$i -lt $lines.Count;$i++){
        $z=[string]$lines[$i]
        if($z -match '(?i)(c1_16_common|def\s+metrics_for\s*\(|def\s+summary_row\s*\(|\ba5b\b)'){
          $refRows+=[pscustomobject]@{
            source="zip";path=$loc;line=$i+1;text=$z.Trim()
          }
        }
      }
    }
  }finally{
    if($zip -ne $null){$zip.Dispose()}
  }
}

$textExt=@(".json",".md",".txt",".tsv",".csv",".yaml",".yml")
$artifactRows=@()
$artifacts=@(
  Get-ChildItem -LiteralPath $Root -File -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object {
    ($textExt -contains $_.Extension.ToLowerInvariant()) -and
    ($_.FullName -notmatch $exclude) -and
    ($_.Length -le 10485760)
  }
)

foreach($f in $artifacts){
  $txt=""
  try{$txt=[string](Get-Content -LiteralPath $f.FullName -Raw)}catch{continue}
  if($txt -notmatch '(?i)(c1_16_common|metrics_for|summary_row|c1_16[a-z0-9_]*\.py|\ba5b\b)'){continue}
  $rel=$f.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")
  $sha=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $lines=@($txt -split "\r?\n")
  $ev=@()
  for($i=0;$i -lt $lines.Count;$i++){
    $z=[string]$lines[$i]
    if($z -match '(?i)(c1_16_common|metrics_for|summary_row|c1_16[a-z0-9_]*\.py|\ba5b\b)'){
      if($ev.Count -lt 30){
        $clean=$z.Trim()
        if($clean.Length -gt 500){$clean=$clean.Substring(0,500)}
        $ev+=("L"+[string]($i+1)+": "+$clean)
      }
    }
  }
  $artifactRows+=[pscustomobject]@{path=$rel;sha256=$sha;bytes=[long]$f.Length;evidence=[string]::Join(" || ",$ev)}
}

$allSources=@($sourceRows)+@($zipEntryRows)
$allSources=@($allSources|Sort-Object source,path -Unique)
$refRows=@($refRows|Sort-Object source,path,line -Unique)
$artifactRows=@($artifactRows|Sort-Object path)

$src=@("source"+$tab+"sha256"+$tab+"bytes"+$tab+"c1_16_common"+$tab+"c1_16_file"+$tab+"metrics_for"+$tab+"summary_row"+$tab+"a5b_ref"+$tab+"imports_c1_16_common"+$tab+"path")
foreach($r in $allSources){
  $src+=([string]$r.source+$tab+[string]$r.sha256+$tab+[string]$r.bytes+$tab+[string]$r.c1_16_common+$tab+[string]$r.c1_16_file+$tab+[string]$r.metrics_for+$tab+[string]$r.summary_row+$tab+[string]$r.a5b_ref+$tab+[string]$r.imports_c1_16_common+$tab+[string]$r.path)
}
[IO.File]::WriteAllText((Join-Path $Out "PYTHON_DEPENDENCY_CANDIDATES.tsv"),([string]::Join($lf,$src)+$lf),$u)

$refs=@("source"+$tab+"line"+$tab+"path"+$tab+"text")
foreach($r in $refRows){
  $safe=([string]$r.text).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
  $refs+=([string]$r.source+$tab+[string]$r.line+$tab+[string]$r.path+$tab+$safe)
}
[IO.File]::WriteAllText((Join-Path $Out "API_REFERENCES.tsv"),([string]::Join($lf,$refs)+$lf),$u)

$arts=@("sha256"+$tab+"bytes"+$tab+"path"+$tab+"evidence")
foreach($r in $artifactRows){
  $safe=([string]$r.evidence).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
  $arts+=([string]$r.sha256+$tab+[string]$r.bytes+$tab+[string]$r.path+$tab+$safe)
}
[IO.File]::WriteAllText((Join-Path $Out "HISTORICAL_ARTIFACT_REFERENCES.tsv"),([string]::Join($lf,$arts)+$lf),$u)

$common=@($allSources|Where-Object{$_.c1_16_common})
$both=@($allSources|Where-Object{$_.metrics_for -and $_.summary_row})
$state=[pscustomobject]@{
  status="READ_ONLY_GLOBAL_DEPENDENCY_HUNT";
  stage11a_freeze_sha256=$S11A;
  loose_python_files_scanned=[int]$py.Count;
  zip_archives_scanned=[int]$zips.Count;
  dependency_source_candidates=[int]$allSources.Count;
  c1_16_common_candidates=[int]$common.Count;
  sources_with_both_metrics_for_and_summary_row=[int]$both.Count;
  api_reference_rows=[int]$refRows.Count;
  historical_artifact_reference_files=[int]$artifactRows.Count;
  training="NONE";
  performance="NONE";
  topology_generation="NONE";
  project_code_execution="NONE";
  archive_extraction="NONE"
}
[IO.File]::WriteAllText((Join-Path $Out "state.json"),(($state|ConvertTo-Json -Depth 5)+$lf),$u)

$report=@(
  "# C1.20P Stage11A2 global dependency hunt",
  "",
  "STATUS: READ-ONLY GLOBAL DEPENDENCY HUNT",
  "Stage11A freeze: "+$S11A,
  "Loose Python files scanned: "+[string]$py.Count,
  "ZIP archives scanned: "+[string]$zips.Count,
  "Dependency source candidates: "+[string]$allSources.Count,
  "c1_16_common candidates: "+[string]$common.Count,
  "Sources with BOTH metrics_for and summary_row: "+[string]$both.Count,
  "API reference rows: "+[string]$refRows.Count,
  "Historical artifact reference files: "+[string]$artifactRows.Count,
  "Training: NONE",
  "Performance: NONE",
  "Topology generation: NONE",
  "Project-code execution: NONE",
  "Archive extraction: NONE",
  "",
  "## Decision boundary",
  "",
  "Stage11B remains unauthorized unless the structural metrics dependency chain can be identified and hash-bound from these results. If the exact historical source is absent, any reconstructed metrics implementation must first reproduce frozen historical structural metrics and topology hashes before the 182xxxx replay is accepted."
)
[IO.File]::WriteAllText((Join-Path $Out "REPORT.md"),([string]::Join($lf,$report)+$lf),$u)

$files=@("API_REFERENCES.tsv","HISTORICAL_ARTIFACT_REFERENCES.tsv","PYTHON_DEPENDENCY_CANDIDATES.tsv","REPORT.md","state.json")
$m=@()
foreach($f in $files){
  $p=Join-Path $Out $f;$i=Get-Item $p;$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  $m+=($h+$tab+[string]$i.Length+$tab+$f)
}
[IO.File]::WriteAllText((Join-Path $Out "stage11a2_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)
$freeze=(Get-FileHash (Join-Path $Out "stage11a2_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE11A2_FREEZE_SHA256.txt"),($freeze+"  stage11a2_manifest.tsv"+$lf),$u)
Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}

Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE11A2 GLOBAL DEPENDENCY HUNT FROZEN"
Write-Host "STAGE11A FREEZE SHA256 : $S11A"
Write-Host "STAGE11A2 FREEZE SHA256: $freeze"
Write-Host "LOOSE PY FILES         : $($py.Count)"
Write-Host "ZIP ARCHIVES            : $($zips.Count)"
Write-Host "DEPENDENCY CANDIDATES   : $($allSources.Count)"
Write-Host "C1_16_COMMON CANDIDATES : $($common.Count)"
Write-Host "BOTH METRICS APIs       : $($both.Count)"
Write-Host "HISTORICAL REF FILES    : $($artifactRows.Count)"
Write-Host "TRAINING                : NONE"
Write-Host "PERFORMANCE             : NONE"
Write-Host "TOPOLOGY GENERATION     : NONE"
Write-Host "PROJECT CODE EXEC       : NONE"
Write-Host "ARCHIVE EXTRACTION      : NONE"
Write-Host ("="*100)
