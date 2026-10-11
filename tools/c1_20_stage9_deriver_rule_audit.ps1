param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage9_deriver_rule_audit_v1"
)

$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

$S8="1527ed75f93e660fd7112d79f20dab4f99501071c98a3e6731387427d4b77b85"
$S8File=Join-Path $Root "07_Resultados\Informes\c1_20p_stage8_selection_logic_evidence_v1\STAGE8_FREEZE_SHA256.txt"
$ZipPath=Join-Path $Root "00_Backup_Drive\RECOVERED_DRIVE_2026-10-01\c1_18p_stage0_v1.zip"
$EntryName="c1_18p_derive_dev_builder.py"
$ExpectedEntrySha="d47fe09e3e23cdad4cf047ed4ccb2945cba3fd81e9fb32630ea0cfe00ac0db4f"

if(-not(Test-Path $S8File)){throw "STAGE8 FREEZE FILE MISSING"}
if((Get-Content $S8File -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S8){throw "STAGE8 FREEZE MISMATCH"}
if(-not(Test-Path $ZipPath)){throw "C1.18P ZIP MISSING"}

if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE9_FREEZE_SHA256.txt")){throw "FROZEN STAGE9 EXISTS"}
  Remove-Item $Out -Recurse -Force
}
New-Item -ItemType Directory -Path $Out|Out-Null

$u=New-Object System.Text.UTF8Encoding($false)
$lf=[char]10
$tab=[char]9

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try{
  $hits=@($zip.Entries|Where-Object{$_.FullName -eq $EntryName})
  if($hits.Count -ne 1){throw "EXPECTED EXACTLY ONE DERIVER ENTRY; FOUND $($hits.Count)"}
  $e=$hits[0]

  $hs=$null;$shaObj=$null
  try{
    $hs=$e.Open()
    $shaObj=[Security.Cryptography.SHA256]::Create()
    $hb=$shaObj.ComputeHash($hs)
    $entrySha=([BitConverter]::ToString($hb)).Replace("-","").ToLowerInvariant()
  }finally{
    if($shaObj -ne $null){$shaObj.Dispose()}
    if($hs -ne $null){$hs.Dispose()}
  }
  if($entrySha -ne $ExpectedEntrySha){throw "DERIVER ENTRY SHA MISMATCH"}

  $s=$null;$r=$null
  try{
    $s=$e.Open()
    $r=New-Object IO.StreamReader($s,[Text.Encoding]::UTF8,$true)
    $text=$r.ReadToEnd()
  }finally{
    if($r -ne $null){$r.Dispose()}elseif($s -ne $null){$s.Dispose()}
  }
}finally{
  $zip.Dispose()
}

$lines=@($text -split "\r?\n")

$Windows=@(
  [pscustomobject]@{name="CONSTANTS_AND_NAMES";start=20;end=45},
  [pscustomobject]@{name="AST_ASSIGN_AND_COMPARE_TRANSFORMS";start=60;end=165},
  [pscustomobject]@{name="NAMESPACE_AND_REQUIRED_PATTERNS";start=166;end=215},
  [pscustomobject]@{name="DERIVATION_MAIN_AND_MANIFEST";start=216;end=315}
)

$outLines=@()
foreach($w in $Windows){
  $outLines+=("===== "+$w.name+" L"+$w.start+"-L"+$w.end+" =====")
  for($n=$w.start;$n -le $w.end;$n++){
    if($n -le $lines.Count){
      $outLines+=("L"+[string]$n+": "+[string]$lines[$n-1])
    }
  }
  $outLines+=""
}
[IO.File]::WriteAllText((Join-Path $Out "DERIVER_WINDOWS.txt"),([string]::Join($lf,$outLines)+$lf),$u)

$decl=@("line"+$tab+"declaration")
for($i=0;$i -lt $lines.Count;$i++){
  $line=[string]$lines[$i]
  if($line -match '^\s*(def|class)\s+[A-Za-z_][A-Za-z0-9_]*'){
    $decl+=([string]($i+1)+$tab+$line.Trim())
  }
}
[IO.File]::WriteAllText((Join-Path $Out "DECLARATIONS.tsv"),([string]::Join($lf,$decl)+$lf),$u)

$terms=@(
  "MIN_DELTA_RDE",
  "RDE_FORMULA",
  "route_hhi is NOT used to choose pairs",
  'x["node_connectivity_mean"]',
  'high["rde"]',
  'low["rde"]',
  "selected_pairs",
  "SEED_START",
  "SEED_END",
  "candidate",
  "pair"
)

$evidence=@("term"+$tab+"line"+$tab+"context")
foreach($term in $terms){
  for($i=0;$i -lt $lines.Count;$i++){
    if(([string]$lines[$i]).Contains($term)){
      $a=[Math]::Max(0,$i-4)
      $b=[Math]::Min($lines.Count-1,$i+4)
      $ctx=@()
      for($j=$a;$j -le $b;$j++){
        $z=([string]$lines[$j]).Trim()
        if($z.Length -gt 500){$z=$z.Substring(0,500)}
        $ctx+=("L"+[string]($j+1)+": "+$z)
      }
      $safe=([string]::Join(" || ",$ctx)).Replace([char]9," ")
      $evidence+=($term+$tab+[string]($i+1)+$tab+$safe)
    }
  }
}
[IO.File]::WriteAllText((Join-Path $Out "TERM_CONTEXT.tsv"),([string]::Join($lf,$evidence)+$lf),$u)

$state=[pscustomobject]@{
  status="READ_ONLY_DERIVER_RULE_AUDIT";
  stage8_freeze_sha256=$S8;
  archive_sha256=(Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant();
  entry_name=$EntryName;
  entry_sha256=$entrySha;
  line_count=[int]$lines.Count;
  training="NONE";
  performance="NONE";
  topology_generation="NONE";
  project_code_execution="NONE";
  archive_extraction="NONE"
}
[IO.File]::WriteAllText((Join-Path $Out "state.json"),(($state|ConvertTo-Json -Depth 4)+$lf),$u)

$rep=@()
$rep+="# C1.20P Stage9 deriver rule audit"
$rep+=""
$rep+="STATUS: READ-ONLY DERIVER SOURCE AUDIT"
$rep+=("Stage8 freeze: "+$S8)
$rep+=("Deriver SHA256: "+$entrySha)
$rep+=("Source lines: "+[string]$lines.Count)
$rep+="Training: NONE"
$rep+="Performance: NONE"
$rep+="Topology generation: NONE"
$rep+="Project-code execution: NONE"
$rep+="Archive extraction: NONE"
$rep+=""
$rep+="## Purpose"
$rep+=""
$rep+="Inspect the surviving C1.18P development deriver itself to expose exactly which historical B1 syntax patterns and cardinalities it recognized and preserved. This audit does not execute the deriver or reconstruct topologies."
$rep+=""
$rep+="## Evidence files"
$rep+=""
$rep+="- DERIVER_WINDOWS.txt: full numbered source windows covering constants, AST transforms, required-pattern assertions, namespace replacements and manifest creation."
$rep+="- TERM_CONTEXT.tsv: context around selection-critical strings."
$rep+="- DECLARATIONS.tsv: function/class declarations."
$rep+=""
$rep+="## Decision boundary"
$rep+=""
$rep+="After Stage9, a reconstructed pairing rule may be implemented only if the deriver source exposes enough historical syntax/semantic constraints to specify grouping, LOW/HIGH assignment, eligibility and final selection order without guessing. Otherwise the unresolved step remains explicit and C1.20 183xxxx stays unauthorized."
[IO.File]::WriteAllText((Join-Path $Out "DERIVER_RULE_AUDIT_REPORT.md"),([string]::Join($lf,$rep)+$lf),$u)

$files=@("DECLARATIONS.tsv","DERIVER_RULE_AUDIT_REPORT.md","DERIVER_WINDOWS.txt","TERM_CONTEXT.tsv","state.json")
$m=@()
foreach($f in $files){
  $p=Join-Path $Out $f;$i=Get-Item $p;$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  $m+=($h+$tab+[string]$i.Length+$tab+$f)
}
[IO.File]::WriteAllText((Join-Path $Out "stage9_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)
$freeze=(Get-FileHash (Join-Path $Out "stage9_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE9_FREEZE_SHA256.txt"),($freeze+"  stage9_manifest.tsv"+$lf),$u)
Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}

Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE9 DERIVER RULE AUDIT FROZEN"
Write-Host "STAGE8 FREEZE SHA256 : $S8"
Write-Host "STAGE9 FREEZE SHA256 : $freeze"
Write-Host "DERIVER SHA256       : $entrySha"
Write-Host "SOURCE LINES         : $($lines.Count)"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host "PROJECT CODE EXEC    : NONE"
Write-Host "ARCHIVE EXTRACTION   : NONE"
Write-Host ("="*100)
