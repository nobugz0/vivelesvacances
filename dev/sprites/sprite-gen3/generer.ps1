# Marine la maline : generation des references de sprites (API Images d'OpenAI), sans Python.
# Etape 1 : Marine (photos de refs\). Etape 2 : planche monde (approved\charref.png seulement).
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.Net.Http

function Fail($msg){ Write-Host ""; Write-Host "ECHEC : $msg" -ForegroundColor Red; exit 1 }

$keyFile = Join-Path $PSScriptRoot '..\cle_openai.txt'
if (-not (Test-Path -LiteralPath $keyFile)) { Fail "cle_openai.txt introuvable a cote du dossier sprite-gen3." }
$key = (Get-Content -LiteralPath $keyFile -Raw).Trim()
if (-not $key.StartsWith('sk-')) { Fail "la cle dans cle_openai.txt ne commence pas par sk-." }

$jobs = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'sheets.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not (Test-Path 'approved\charref.png')) { $id = 'charref' }
elseif (-not (Test-Path 'approved\world.png')) { $id = 'world' }
else { Write-Host "Les deux references sont deja validees : rien a faire."; exit 0 }
$job = $jobs | Where-Object { $_.id -eq $id }

# les images envoyees : les photos de refs\ (sauf si le job dit photos: false), puis les references validees
$files = @()
if ($job.photos -ne $false) { $files += Get-ChildItem -LiteralPath 'refs' -File | Where-Object { $_.Extension -match '^\.(png|jpe?g|webp)$' } | ForEach-Object { $_.FullName } }
foreach ($dep in @($job.uses)) { if ($dep) { $p = Join-Path $PSScriptRoot "approved\$dep.png"; if (-not (Test-Path -LiteralPath $p)) { Fail "il manque approved\$dep.png" }; $files += $p } }
if ($files.Count -eq 0) { Fail "aucune image de reference dans refs\" }

Write-Host ""
Write-Host "=== $($job.name) : 3 variantes, compte une a trois minutes ===" -ForegroundColor Cyan
Write-Host ("references envoyees : " + (($files | ForEach-Object { Split-Path $_ -Leaf }) -join ', '))

function Send($model, $fidelity){
  $client = New-Object System.Net.Http.HttpClient
  $client.Timeout = [TimeSpan]::FromSeconds(600)
  $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $key)
  $form = New-Object System.Net.Http.MultipartFormDataContent
  $fields = [ordered]@{ model = $model; prompt = $job.prompt; size = $job.size; quality = 'high'; n = '3'; output_format = 'png' }
  if ($fidelity) { $fields['input_fidelity'] = 'high' }
  # noms de champs entre guillemets, ecrits a la main : .NET Framework ne les met pas, et image[] doit l'etre
  foreach ($k in $fields.Keys) { $sc = New-Object System.Net.Http.StringContent([string]$fields[$k], [Text.Encoding]::UTF8); $sc.Headers.ContentType = $null; $cd = New-Object System.Net.Http.Headers.ContentDispositionHeaderValue('form-data'); $cd.Name = '"' + $k + '"'; $sc.Headers.ContentDisposition = $cd; $form.Add($sc) }
  foreach ($f in $files) {
    $bc = New-Object System.Net.Http.ByteArrayContent(,[IO.File]::ReadAllBytes($f))
    $ext = [IO.Path]::GetExtension($f).ToLower(); $mime = @{ '.png'='image/png'; '.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.webp'='image/webp' }[$ext]
    $bc.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue($mime)
    $cd = New-Object System.Net.Http.Headers.ContentDispositionHeaderValue('form-data'); $cd.Name = '"image[]"'; $cd.FileName = '"' + [IO.Path]::GetFileName($f) + '"'; $bc.Headers.ContentDisposition = $cd; $form.Add($bc)
  }
  try { $r = $client.PostAsync('https://api.openai.com/v1/images/edits', $form).GetAwaiter().GetResult() }
  catch { return @{ code = 0; body = $_.Exception.GetBaseException().Message } }
  $body = $r.Content.ReadAsStringAsync().GetAwaiter().GetResult()
  $client.Dispose()
  return @{ code = [int]$r.StatusCode; body = $body }
}

$model = 'gpt-image-2'; $fidelity = $true; $res = $null
for ($attempt = 1; $attempt -le 4; $attempt++) {
  $t0 = Get-Date
  $res = Send $model $fidelity
  if ($res.code -eq 200) { break }
  $short = if ($res.body.Length -gt 600) { $res.body.Substring(0, 600) } else { $res.body }
  if ($res.code -eq 400 -and $fidelity -and $res.body -match 'input_fidelity') { Write-Host "le modele refuse input_fidelity, nouvel essai sans"; $fidelity = $false; continue }
  if (($res.code -eq 400 -or $res.code -eq 404) -and $model -eq 'gpt-image-2' -and $res.body -match 'model') { Write-Host "gpt-image-2 indisponible, nouvel essai avec gpt-image-1"; $model = 'gpt-image-1'; continue }
  if (($res.code -eq 0 -or $res.code -eq 429 -or $res.code -ge 500) -and $attempt -lt 4) { Write-Host "erreur $($res.code), nouvel essai dans $(10*$attempt) s"; Start-Sleep -Seconds (10*$attempt); continue }
  Fail "HTTP $($res.code) : $short"
}
if ($res.code -ne 200) { Fail "pas de reponse valide apres plusieurs essais" }

New-Item -ItemType Directory -Force -Path 'output' | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$m = [regex]::Matches($res.body, '"b64_json"\s*:\s*"([^"]+)"')
if ($m.Count -eq 0) { Fail "reponse sans image : $($res.body.Substring(0, [Math]::Min(400, $res.body.Length)))" }
$i = 0
foreach ($x in $m) { $i++; $out = Join-Path $PSScriptRoot "output\$($id)_$($stamp)_v$i.png"; [IO.File]::WriteAllBytes($out, [Convert]::FromBase64String($x.Groups[1].Value.Replace('\/', '/'))); Write-Host "enregistre : output\$(Split-Path $out -Leaf)" -ForegroundColor Green }
Write-Host ("fait en {0:N0} s avec {1}" -f ((Get-Date) - $t0).TotalSeconds, $model)
exit 0
