# Marine la maline : generation des sons (API ElevenLabs), sans Python.
# Lit sons.json ; genere ce qui manque dans output\ pour le lot indique dans lot.txt (par defaut "test").
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
function Fail($msg){ Write-Host ""; Write-Host "ECHEC : $msg" -ForegroundColor Red; exit 1 }
$keyFile = Join-Path $PSScriptRoot '..\cle_elevenlabs.txt'
if (-not (Test-Path -LiteralPath $keyFile)) { Fail "cle_elevenlabs.txt introuvable dans le dossier Marine La Maline." }
$key = (Get-Content -LiteralPath $keyFile -Raw).Trim()
$lot = if (Test-Path 'lot.txt') { (Get-Content 'lot.txt' -Raw).Trim() } else { 'test' }
$jobs = Get-Content -LiteralPath 'sons.json' -Raw -Encoding UTF8 | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path 'output' | Out-Null

function Post($url, $obj, $out){
  $json = $obj | ConvertTo-Json -Depth 12 -Compress
  try {
    Invoke-WebRequest -Uri $url -Method Post -UseBasicParsing -Headers @{ 'xi-api-key' = $key } -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json)) -OutFile $out -TimeoutSec 600 | Out-Null
    return $null
  } catch {
    $msg = $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $msg = $msg + ' ' + $_.ErrorDetails.Message } else { try { $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream()); $msg = $msg + ' ' + $sr.ReadToEnd() } catch {} }
    if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -ErrorAction SilentlyContinue }
    return $msg
  }
}

$todo = @($jobs | Where-Object { $_.batch -eq $lot })
Write-Host ("Lot '{0}' : {1} element(s)" -f $lot, $todo.Count) -ForegroundColor Cyan
$ok = 0; $ko = 0
foreach ($j in $todo) {
  $n = if ($j.n) { [int]$j.n } else { 1 }
  $models = if ($j.type -eq 'sfx') { @($j.models) } else { @($j.model_id) }
  foreach ($m in $models) { for ($v = 1; $v -le $n; $v++) {
    $tag = if ($j.type -eq 'sfx') { ($m -replace 'eleven_text_to_sound_', '') } else { $m }
    $out = Join-Path $PSScriptRoot ("output\{0}_{1}_v{2}.mp3" -f $j.id, $tag, $v)
    if (Test-Path -LiteralPath $out) { continue }
    Write-Host ("{0} ({1}, variante {2})..." -f $j.id, $tag, $v)
    $err = $null
    for ($try = 1; $try -le 4; $try++) {   # surcharge passagere (429, 5xx) : on attend et on recommence
    if ($j.type -eq 'sfx') {
      $body = [ordered]@{ text = $j.text; duration_seconds = $j.duration_seconds; prompt_influence = $j.prompt_influence; loop = [bool]$j.loop; model_id = $m }
      $err = Post 'https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128' $body $out
    } else {
      $body = [ordered]@{ composition_plan = $j.composition_plan; model_id = $m }
      $err = Post 'https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192' $body $out
    }
    if ($err -and ($err -match '\(429\)|\(5\d\d\)') -and $try -lt 4) { Write-Host ("  surcharge, nouvel essai dans {0} s" -f (20*$try)); Start-Sleep -Seconds (20*$try); continue }
    break }
    if ($err) { $ko++; Write-Host ("ECHEC {0} : {1}" -f $j.id, $err) -ForegroundColor Red; Add-Content -LiteralPath 'output\erreurs.txt' -Value ("{0} {1} {2} : {3}" -f (Get-Date -Format s), $j.id, $tag, $err) }
    else { $ok++; Write-Host ("  enregistre : {0}" -f (Split-Path $out -Leaf)) -ForegroundColor Green }
  } }
}
Write-Host ""
Write-Host ("Bilan : {0} fichier(s), {1} echec(s)." -f $ok, $ko)
if ($ko -gt 0) { exit 1 } else { exit 0 }
