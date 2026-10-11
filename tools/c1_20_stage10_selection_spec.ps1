param(
  [string]$Root="C:\ABGEN",
  [string]$Out="C:\ABGEN\07_Resultados\Informes\c1_20p_stage10_selection_spec_v1"
)

$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

$S9="8392f40d25e3745da8fef26403916f05e765f2053bad19331b7d6c570688e165"
$S9File=Join-Path $Root "07_Resultados\Informes\c1_20p_stage9_deriver_rule_audit_v1\STAGE9_FREEZE_SHA256.txt"

if(-not(Test-Path $S9File)){throw "STAGE9 FREEZE FILE MISSING"}
if((Get-Content $S9File -Raw).Trim().Split()[0].ToLowerInvariant() -ne $S9){throw "STAGE9 FREEZE MISMATCH"}

if(Test-Path $Out){
  if(Test-Path (Join-Path $Out "STAGE10_FREEZE_SHA256.txt")){throw "FROZEN STAGE10 EXISTS"}
  Remove-Item $Out -Recurse -Force
}
New-Item -ItemType Directory -Path $Out|Out-Null

$u=New-Object System.Text.UTF8Encoding($false)
$lf=[char]10
$tab=[char]9

$spec=[pscustomobject]@{
  status="RECOVERED_RECONSTRUCTED_SELECTION_SPEC"
  stage9_freeze_sha256=$S9
  provenance=[pscustomobject]@{
    historical_source_byte_exact_available=$false
    historical_b1_expected_sha256="732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463"
    classification="RECOVERED_RECONSTRUCTED"
  }
  rde=[pscustomobject]@{
    formula="(1-route_top3_share)/mean_distance"
    min_delta=0.015
    route_hhi_used_for_selection=$false
  }
  eligibility=[pscustomobject]@{
    exact_match=@("global_vertex_cut","global_edge_cut","node_connectivity_mean")
    max_abs_delta_changed_fraction=0.02
    min_delta_rde=0.015
    low_high_definition="LOW=lower RDE; HIGH=higher RDE"
  }
  ordering=@(
    "abs_delta_changed_fraction ASC",
    "delta_rde DESC",
    "LOW_seed ASC",
    "HIGH_seed ASC"
  )
  greedy=[pscustomobject]@{
    unique_topology_across_pairs=$true
    max_pairs_per_exact_stratum=2
    stratum_fields=@("global_vertex_cut","global_edge_cut","node_connectivity_mean")
    stop_at_target_pairs=$true
  }
  historical_replay=[pscustomobject]@{
    seed_start=1820000
    seed_end=1820399
    candidates=400
    eligible_pairs=91
    selected_pairs=16
    selected_topologies=32
  }
  future_c1_20=[pscustomobject]@{
    seed_start=1830000
    seed_end=1830399
    candidates=400
    target_pairs=16
    target_topologies=32
    range_extension=$false
    reseeding=$false
    threshold_relaxation=$false
    performance_rescue=$false
  }
  training="NONE"
  performance="NONE"
  topology_generation="NONE"
}

[IO.File]::WriteAllText((Join-Path $Out "SELECTION_SPEC.json"),(($spec|ConvertTo-Json -Depth 8)+$lf),$u)

$report=@(
  "# C1.20P Stage10 reconstructed selection specification",
  "",
  "STATUS: RECOVERED/RECONSTRUCTED SELECTION SPEC",
  "Stage9 freeze: "+$S9,
  "Historical byte-exact B1 source: NO",
  "RDE: (1-route_top3_share)/mean_distance",
  "MIN_DELTA_RDE: 0.015",
  "Exact pair stratum: global_vertex_cut + global_edge_cut + node_connectivity_mean",
  "MAX_ABS_DELTA_CHANGED_FRACTION: 0.020000",
  "LOW/HIGH: by RDE only",
  "Eligible ordering: abs_delta_changed_fraction ASC; delta_rde DESC; LOW_seed ASC; HIGH_seed ASC",
  "Greedy uniqueness: YES",
  "Max pairs per exact stratum: 2",
  "Historical replay target: 1820000..1820399 => 400 candidates => 91 eligible => 16 pairs / 32 topologies",
  "Future C1.20 target after replay PASS: 1830000..1830399 => 400 candidates => 16 pairs / 32 topologies",
  "Range extension: NO",
  "Reseeding: NO",
  "Threshold relaxation: NO",
  "Performance rescue: NO",
  "Training: NONE",
  "Performance: NONE",
  "Topology generation: NONE"
)
[IO.File]::WriteAllText((Join-Path $Out "REPORT.md"),([string]::Join($lf,$report)+$lf),$u)

$files=@("REPORT.md","SELECTION_SPEC.json")
$m=@()
foreach($f in $files){
  $p=Join-Path $Out $f
  $i=Get-Item $p
  $h=(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()
  $m+=($h+$tab+[string]$i.Length+$tab+$f)
}
[IO.File]::WriteAllText((Join-Path $Out "stage10_manifest.tsv"),([string]::Join($lf,$m)+$lf),$u)

$freeze=(Get-FileHash (Join-Path $Out "stage10_manifest.tsv") -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Out "STAGE10_FREEZE_SHA256.txt"),($freeze+"  stage10_manifest.tsv"+$lf),$u)

Get-ChildItem $Out -File|ForEach-Object{$_.IsReadOnly=$true}

Write-Host ("="*100)
Write-Host "PASS: C1.20P STAGE10 SELECTION SPEC FROZEN"
Write-Host "STAGE9 FREEZE SHA256  : $S9"
Write-Host "STAGE10 FREEZE SHA256 : $freeze"
Write-Host "HISTORICAL REPLAY     : 400 -> 91 -> 16 / 32"
Write-Host "ORDER                  : abs_dCF ASC, dRDE DESC, LOW seed ASC, HIGH seed ASC"
Write-Host "MAX PAIRS / STRATUM    : 2"
Write-Host "TRAINING               : NONE"
Write-Host "PERFORMANCE            : NONE"
Write-Host "TOPOLOGY GENERATION    : NONE"
Write-Host ("="*100)
