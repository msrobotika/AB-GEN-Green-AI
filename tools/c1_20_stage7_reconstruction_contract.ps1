param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage7_reconstruction_contract_v1"
)
$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest
$S6="0dafe2936e73bc8df38e46c176a6f0346f2b0005d56c37f6e938151ce78bcd75"
$S6File=Join-Path $Root "07_Resultados\Informes\c1_20p_stage6_exhaustive_hash_hunt_v1\STAGE6_FREEZE_SHA256.txt"
if((Get-Content $S6File -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S6){throw "STAGE6 FREEZE MISMATCH"}
if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE7_FREEZE_SHA256.txt")){throw "FROZEN STAGE7 EXISTS"}
  Remove-Item $Out -Recurse -Force
}
$Pkg=Join-Path $Root "04_Codigo\training\c1_19r_recovery"
$Req=@{
 "c1_19r_recovery_runner.py"="5522b3cc5a49aec7bd53282f1a54b2bc97f0194f9221124fbe7f664290d41929"
 "recovery_evidence.json"="28d7b81ebeada8a78a0024a318d0e8f74595e0fa5cb695e99cb5fc95ec0ec1bd"
 "selected_pairs_recovered.json"="02a44ac1e21a14d1c64f2470f21f35cb8d70b7c32ff4acd0e4f9075d1c2df76b"
}
foreach($k in $Req.Keys){
  $p=Join-Path $Pkg $k
  if(-not(Test-Path $p)){throw "MISSING $k"}
  $h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  if($h -ne $Req[$k]){throw "SHA MISMATCH $k"}
}
$E=Get-Content (Join-Path $Pkg "recovery_evidence.json") -Raw|ConvertFrom-Json
$PairsRoot=Get-Content (Join-Path $Pkg "selected_pairs_recovered.json") -Raw|ConvertFrom-Json

function Find-JsonProperty {
  param($Node,[string]$Name)
  $Found=@()
  if($null -eq $Node){return $Found}
  if($Node -is [System.Array]){
    foreach($Item in $Node){$Found+=@(Find-JsonProperty $Item $Name)}
    return $Found
  }
  if($Node -is [System.Management.Automation.PSCustomObject]){
    foreach($Prop in $Node.PSObject.Properties){
      if($Prop.Name -eq $Name){$Found+=,$Prop.Value}
      if(($Prop.Value -is [System.Management.Automation.PSCustomObject]) -or ($Prop.Value -is [System.Array])){
        $Found+=@(Find-JsonProperty $Prop.Value $Name)
      }
    }
  }
  return $Found
}

$ReplayHits=@(Find-JsonProperty $E "c1_18_confirmation_replay")
if($ReplayHits.Count -ne 1){throw "EXPECTED EXACTLY 1 c1_18_confirmation_replay; FOUND $($ReplayHits.Count)"}
$R=$ReplayHits[0]

function Find-PairCollections {
  param($Node)
  $Found=@()
  if($null -eq $Node){return $Found}

  if($Node -is [System.Array]){
    $Items=@($Node)
    if($Items.Count -eq 16){
      $Ok=$true
      foreach($Item in $Items){
        if(-not($Item -is [System.Management.Automation.PSCustomObject])){
          $Ok=$false
          break
        }
        $Names=@($Item.PSObject.Properties | ForEach-Object {$_.Name})
        if(-not(($Names -contains "low") -and ($Names -contains "high") -and ($Names -contains "delta_rde"))){
          $Ok=$false
          break
        }
      }
      if($Ok){
        $Found += [pscustomobject]@{pairs=$Items}
      }
    }
    foreach($Item in $Items){
      $Found += @(Find-PairCollections $Item)
    }
    return $Found
  }

  if($Node -is [System.Management.Automation.PSCustomObject]){
    foreach($Prop in $Node.PSObject.Properties){
      if(($Prop.Value -is [System.Management.Automation.PSCustomObject]) -or ($Prop.Value -is [System.Array])){
        $Found += @(Find-PairCollections $Prop.Value)
      }
    }
  }
  return $Found
}

$PairHits=@(Find-PairCollections $PairsRoot)
if($PairHits.Count -ne 1){throw "EXPECTED EXACTLY 1 RECOVERED 16-PAIR COLLECTION; FOUND $($PairHits.Count)"}
$P=@($PairHits[0].pairs)

if([int]$R.candidate_count -ne 400){throw "candidate_count"}
if([int]$R.eligible_pair_count -ne 91){throw "eligible_pair_count"}
if(@($R.selected_pairs).Count -ne 16){throw "replay selected_pairs"}
if($P.Count -ne 16){throw "recovered pair count after structural extraction"}
$seeds=@{};$hashes=@{};$rows=@()
for($i=0;$i -lt 16;$i++){
  $x=$P[$i]
  if([double]$x.delta_rde -lt 0.015){throw "delta threshold"}
  foreach($side in @("low","high")){
    $v=$x.$side;$seed=[string]$v.seed;$sha=[string]$v.topology_sha256
    if($seeds.ContainsKey($seed)){throw "duplicate seed $seed"}
    if($hashes.ContainsKey($sha)){throw "duplicate topology $sha"}
    $seeds[$seed]=$true;$hashes[$sha]=$true
  }
  if([Math]::Abs([double]$R.selected_pairs[$i].delta_rde-[double]$x.delta_rde)-gt 1e-15){throw "delta mismatch $i"}
  $rows+=[pscustomobject]@{
    pair=$i+1;delta_rde=[double]$x.delta_rde;
    low_seed=[int]$x.low.seed;low_sha=[string]$x.low.topology_sha256;
    high_seed=[int]$x.high.seed;high_sha=[string]$x.high.topology_sha256
  }
}
if($seeds.Count -ne 32 -or $hashes.Count -ne 32){throw "expected 32 unique seeds/hashes"}
New-Item -ItemType Directory -Path $Out|Out-Null
$u=New-Object System.Text.UTF8Encoding($false);$lf=[char]10;$tab=[char]9
$c=[pscustomobject]@{
 status="RECOVERED_RECONSTRUCTED_ONLY";stage6_freeze_sha256=$S6;
 byte_exact_historical_source_available=$false;
 replay=[pscustomobject]@{seed_start=1820000;seed_end=1820399;candidates=400;eligible_pairs=91;pairs=16;topologies=32;min_delta_rde=0.015};
 locks=[pscustomobject]@{rde_formula="(1-route_top3_share)/mean_distance";route_hhi_selection=$false;performance_selection=$false;fle_selection=$false;kmnist_selection=$false;training_selection=$false};
 future=[pscustomobject]@{seed_start=1830000;seed_end=1830399;candidates=400;target_pairs=16;target_topologies=32;range_extension=$false};
 training="NONE";performance="NONE";topology_generation="NONE"
}
[IO.File]::WriteAllText((Join-Path $Out "RECONSTRUCTION_CONTRACT.json"),(($c|ConvertTo-Json -Depth 6)+$lf),$u)
$l=@("pair"+$tab+"delta_rde"+$tab+"low_seed"+$tab+"low_sha"+$tab+"high_seed"+$tab+"high_sha")
foreach($r in $rows){$l+=([string]$r.pair+$tab+[string]$r.delta_rde+$tab+[string]$r.low_seed+$tab+[string]$r.low_sha+$tab+[string]$r.high_seed+$tab+[string]$r.high_sha)}
[IO.File]::WriteAllText((Join-Path $Out "HISTORICAL_CONFIRMATION_PAIRS.tsv"),([string]::Join($lf,$l)+$lf),$u)
$rep=@("# C1.20 Stage7 reconstruction contract","","STATUS: RECOVERED/RECONSTRUCTED ONLY","Stage6: "+$S6,"Historical byte-exact source: NO","Replay gate: 400 -> 91 -> 16 pairs / 32 topologies","Unique recovered seeds: 32","Unique recovered topology hashes: 32","MIN_DELTA_RDE: 0.015","C1.20 future seeds: 1830000..1830399","Range extension: NO","Training: NONE","Performance: NONE","Topology generation: NONE")
[IO.File]::WriteAllText((Join-Path $Out "REPORT.md"),([string]::Join($lf,$rep)+$lf),$u)
$files=@("HISTORICAL_CONFIRMATION_PAIRS.tsv","RECONSTRUCTION_CONTRACT.json","REPORT.md")
$m=@();foreach($f in $files){$p=Join-Path $Out $f;$i=Get-Item $p;$h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant();$m+=($h+$tab+[string]$i.Length+$tab+$f)}
[IO.File]::WriteAllText((Join-Path $Out "stage7_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)
$freeze=(Get-FileHash (Join-Path $Out "stage7_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE7_FREEZE_SHA256.txt"),($freeze+"  stage7_manifest.tsv"+$lf),$u)
Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}
Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE7 RECONSTRUCTION CONTRACT FROZEN"
Write-Host "STAGE6 FREEZE SHA256 : $S6"
Write-Host "STAGE7 FREEZE SHA256 : $freeze"
Write-Host "REPLAY CONTRACT      : 400 -> 91 -> 16 / 32"
Write-Host "UNIQUE SEEDS         : $($seeds.Count)"
Write-Host "UNIQUE TOPO HASHES   : $($hashes.Count)"
Write-Host "HISTORICAL SOURCE    : NOT BYTE-EXACT AVAILABLE"
Write-Host "TRAINING             : NONE"
Write-Host "PERFORMANCE          : NONE"
Write-Host "TOPOLOGY GENERATION  : NONE"
Write-Host ("="*100)
