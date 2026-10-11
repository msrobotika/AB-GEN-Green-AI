param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage8_selection_logic_evidence_v1"
)
$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

$S7="7ad3b78dd9206c9808bcaf8824a3ae87dd4d282e62c8cd8eb0268091b32d7efb"
$S7File=Join-Path $Root "07_Resultados\Informes\c1_20p_stage7_reconstruction_contract_v1\STAGE7_FREEZE_SHA256.txt"
if(-not(Test-Path $S7File)){throw "STAGE7 FREEZE FILE MISSING"}
if((Get-Content $S7File -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S7){throw "STAGE7 FREEZE MISMATCH"}

if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE8_FREEZE_SHA256.txt")){throw "FROZEN STAGE8 EXISTS"}
  Remove-Item $Out -Recurse -Force
}
New-Item -ItemType Directory -Path $Out|Out-Null

$u=New-Object System.Text.UTF8Encoding($false)
$lf=[char]10
$tab=[char]9

$Cats=@(
  [pscustomobject]@{name="GENERATION";rx='(?i)(SEED_START|SEED_END|candidate|topology_seed|build_flycore|build_.*topolog|edge_hash|mask_to_edges|edges_to_mask)'},
  [pscustomobject]@{name="RDE";rx='(?i)(route_top3_share|mean_distance|RDE_FORMULA|delta_rde|["'']rde["''])'},
  [pscustomobject]@{name="ELIGIBILITY";rx='(?i)(MIN_DELTA_RDE|eligible|eligibility|node_connectivity_mean|filter|threshold)'},
  [pscustomobject]@{name="PAIRING";rx='(?i)(selected_pairs|selected|pair|low["'']|high["'']|sort|sorted|used|combinations)'},
  [pscustomobject]@{name="PROVENANCE";rx='(?i)(c1_17b1_independent_bank|historical B1|derived builder|recovery|reconstruct)'}
)

$Exts=@(".py",".ps1",".json",".md",".txt",".csv",".tsv",".yaml",".yml")
$ExcludeRx='(?i)(\\\.venv\\|\\__pycache__\\|\\c1_20p_stage[0-9])'
$Rows=@()
$FileRows=@()

$Files=@(
  Get-ChildItem -LiteralPath $Root -File -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object {
    ($Exts -contains $_.Extension.ToLowerInvariant()) -and
    ($_.FullName -notmatch $ExcludeRx) -and
    ($_.Length -le 5242880)
  }
)

foreach($F in $Files){
  $Rel=$F.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")
  $Text=""
  try{$Text=[string](Get-Content -LiteralPath $F.FullName -Raw)}catch{continue}
  $Any=$false
  foreach($C in $Cats){
    if($Text -notmatch $C.rx){continue}
    $Any=$true
    $Lines=@($Text -split "\r?\n")
    $Hits=0
    for($i=0;$i -lt $Lines.Count;$i++){
      if($Lines[$i] -match $C.rx){
        $start=[Math]::Max(0,$i-2)
        $end=[Math]::Min($Lines.Count-1,$i+2)
        $ctx=@()
        for($j=$start;$j -le $end;$j++){
          $z=([string]$Lines[$j]).Trim()
          if($z.Length -gt 420){$z=$z.Substring(0,420)}
          $ctx+=("L"+[string]($j+1)+": "+$z)
        }
        $Rows+=[pscustomobject]@{
          source="loose";location=$Rel;category=$C.name;line=$i+1;
          context=[string]::Join(" || ",$ctx)
        }
        $Hits++
        if($Hits -ge 20){break}
      }
    }
  }
  if($Any){
    $FileRows+=[pscustomobject]@{
      source="loose";location=$Rel;sha256=(Get-FileHash $F.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=[long]$F.Length
    }
  }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$ZipFiles=@(Get-ChildItem -LiteralPath $Root -File -Recurse -Force -Filter *.zip -ErrorAction SilentlyContinue)
$ZipEntryCount=0

foreach($ZF in $ZipFiles){
  $Zip=$null
  try{
    $Zip=[System.IO.Compression.ZipFile]::OpenRead($ZF.FullName)
    foreach($E in $Zip.Entries){
      if([string]::IsNullOrWhiteSpace($E.Name)){continue}
      $ext=[IO.Path]::GetExtension($E.Name).ToLowerInvariant()
      if(-not($Exts -contains $ext)){continue}
      if($E.Length -gt 5242880){continue}
      $s=$null;$r=$null;$Text=""
      try{
        $s=$E.Open()
        $r=New-Object IO.StreamReader($s,[Text.Encoding]::UTF8,$true)
        $Text=$r.ReadToEnd()
      }finally{
        if($r -ne $null){$r.Dispose()}elseif($s -ne $null){$s.Dispose()}
      }
      $Any=$false
      foreach($C in $Cats){
        if($Text -notmatch $C.rx){continue}
        $Any=$true
        $Lines=@($Text -split "\r?\n")
        $Hits=0
        for($i=0;$i -lt $Lines.Count;$i++){
          if($Lines[$i] -match $C.rx){
            $start=[Math]::Max(0,$i-2)
            $end=[Math]::Min($Lines.Count-1,$i+2)
            $ctx=@()
            for($j=$start;$j -le $end;$j++){
              $z=([string]$Lines[$j]).Trim()
              if($z.Length -gt 420){$z=$z.Substring(0,420)}
              $ctx+=("L"+[string]($j+1)+": "+$z)
            }
            $Rows+=[pscustomobject]@{
              source="zip";location=($ZF.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")+"::"+$E.FullName);
              category=$C.name;line=$i+1;context=[string]::Join(" || ",$ctx)
            }
            $Hits++
            if($Hits -ge 20){break}
          }
        }
      }
      if($Any){
        $hs=$null;$shaObj=$null
        try{
          $hs=$E.Open()
          $shaObj=[Security.Cryptography.SHA256]::Create()
          $hb=$shaObj.ComputeHash($hs)
          $eh=([BitConverter]::ToString($hb)).Replace("-","").ToLowerInvariant()
        }finally{
          if($shaObj -ne $null){$shaObj.Dispose()}
          if($hs -ne $null){$hs.Dispose()}
        }
        $FileRows+=[pscustomobject]@{
          source="zip";location=($ZF.FullName.Substring($Root.Length).TrimStart("\").Replace("\","/")+"::"+$E.FullName);
          sha256=$eh;bytes=[long]$E.Length
        }
        $ZipEntryCount++
      }
    }
  }finally{
    if($Zip -ne $null){$Zip.Dispose()}
  }
}

$Rows=@($Rows|Sort-Object category,source,location,line)
$FileRows=@($FileRows|Sort-Object source,location -Unique)

$ev=@("source"+$tab+"category"+$tab+"line"+$tab+"location"+$tab+"context")
foreach($R in $Rows){
  $safe=([string]$R.context).Replace([char]9," ").Replace([char]13," ").Replace([char]10," ")
  $ev+=([string]$R.source+$tab+[string]$R.category+$tab+[string]$R.line+$tab+[string]$R.location+$tab+$safe)
}
[IO.File]::WriteAllText((Join-Path $Out "logic_evidence.tsv"),([string]::Join($lf,$ev)+$lf),$u)

$fl=@("source"+$tab+"sha256"+$tab+"bytes"+$tab+"location")
foreach($R in $FileRows){$fl+=([string]$R.source+$tab+[string]$R.sha256+$tab+[string]$R.bytes+$tab+[string]$R.location)}
[IO.File]::WriteAllText((Join-Path $Out "evidence_sources.tsv"),([string]::Join($lf,$fl)+$lf),$u)

$state=[pscustomobject]@{
  status="READ_ONLY_SELECTION_LOGIC_EVIDENCE";
  stage7_freeze_sha256=$S7;
  loose_files_considered=[int]$Files.Count;
  zip_archives=[int]$ZipFiles.Count;
  zip_entries_with_evidence=[int]$ZipEntryCount;
  evidence_sources=[int]$FileRows.Count;
  evidence_rows=[int]$Rows.Count;
  training="NONE";performance="NONE";topology_generation="NONE";project_code_execution="NONE";archive_extraction="NONE"
}
[IO.File]::WriteAllText((Join-Path $Out "state.json"),(($state|ConvertTo-Json -Depth 5)+$lf),$u)

$report=@()
$report+="# C1.20P Stage8 selection-logic evidence"
$report+=""
$report+="STATUS: READ-ONLY SOURCE-EVIDENCE EXTRACTION"
$report+=("Stage7 freeze: "+$S7)
$report+=("Evidence sources: "+[string]$FileRows.Count)
$report+=("Evidence rows: "+[string]$Rows.Count)
$report+=("ZIP archives inspected: "+[string]$ZipFiles.Count)
$report+="Training: NONE"
$report+="Performance: NONE"
$report+="Topology generation: NONE"
$report+="Project-code execution: NONE"
$report+="Archive extraction: NONE"
$report+=""
$report+="## Highest-value evidence"
$report+=""

$Priority=@(
  "c1_17b1_independent_bank",
  "c1_18p_derive_dev_builder",
  "c1_19r_recovery",
  "selected_pairs",
  "route_top3_share",
  "node_connectivity_mean",
  "MIN_DELTA_RDE"
)

$Picked=@()
foreach($Ptn in $Priority){
  $Picked+=@($Rows|Where-Object{($_.location -match [Regex]::Escape($Ptn)) -or ($_.context -match [Regex]::Escape($Ptn))}|Select-Object -First 25)
}
$Picked=@($Picked|Sort-Object category,source,location,line -Unique)

foreach($R in $Picked){
  $report+=("["+$R.category+"] "+$R.location+" @L"+[string]$R.line)
  $report+=[string]$R.context
  $report+=""
}

$report+="## Decision boundary"
$report+=""
$report+="Stage8 extracts surviving source evidence only. A reconstructed selection rule may be implemented only from source-supported semantics. If the complete candidate->eligible->LOW/HIGH pairing->selection rule is not supported, the missing step must remain explicit and C1.20 183xxxx generation stays unauthorized."
[IO.File]::WriteAllText((Join-Path $Out "LOGIC_EVIDENCE_REPORT.md"),([string]::Join($lf,$report)+$lf),$u)

$files=@("LOGIC_EVIDENCE_REPORT.md","evidence_sources.tsv","logic_evidence.tsv","state.json")
$m=@()
foreach($f in $files){
  $p=Join-Path $Out $f;$i=Get-Item $p;$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  $m+=($h+$tab+[string]$i.Length+$tab+$f)
}
[IO.File]::WriteAllText((Join-Path $Out "stage8_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)
$freeze=(Get-FileHash (Join-Path $Out "stage8_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE8_FREEZE_SHA256.txt"),($freeze+"  stage8_manifest.tsv"+$lf),$u)
Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}

Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE8 SELECTION LOGIC EVIDENCE FROZEN"
Write-Host "STAGE7 FREEZE SHA256 : $S7"
Write-Host "STAGE8 FREEZE SHA256 : $freeze"
Write-Host "EVIDENCE SOURCES     : $($FileRows.Count)"
Write-Host "EVIDENCE ROWS        : $($Rows.Count)"
Write-Host "ZIP ARCHIVES         : $($ZipFiles.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("="*100)
