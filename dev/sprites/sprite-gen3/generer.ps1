# Marine la maline : generation des sprites (API Images d'OpenAI), sans Python.
# 1) charref (Marine)  2) world (planche monde)  3) toutes les planches "batch" qui n'ont pas encore d'image dans output\
#    Pour refaire une planche, Claude deplace ses images dans output\_rejet : le prochain double-clic la regenere.
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
New-Item -ItemType Directory -Force -Path 'output' | Out-Null

function RefFiles($job){
  $files = @()
  if ($job.photos -ne $false) {
    $dir = if ($job.refdir) { $job.refdir } else { 'refs' }
    $files += Get-ChildItem -LiteralPath $dir -File | Where-Object { $_.Extension -match '^\.(png|jpe?g|webp)$' } | ForEach-Object { $_.FullName }
  }
  foreach ($dep in @($job.uses)) { if ($dep) { $p = Join-Path $PSScriptRoot "approved\$dep.png"; if (-not (Test-Path -LiteralPath $p)) { Fail "il manque approved\$dep.png" }; $files += $p } }
  foreach ($x in @($job.extra)) { if ($x) { $p = Join-Path $PSScriptRoot $x; if (-not (Test-Path -LiteralPath $p)) { Fail "il manque $x" }; $files += $p } }
  if ($files.Count -eq 0) { Fail "aucune image de reference pour $($job.id)" }
  return ,$files
}

function Send($job, $files, $n, $model, $fidelity){
  $client = New-Object System.Net.Http.HttpClient
  $client.Timeout = [TimeSpan]::FromSeconds(900)
  $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $key)
  $form = New-Object System.Net.Http.MultipartFormDataContent
  $fields = [ordered]@{ model = $model; prompt = $job.prompt; size = $job.size; quality = 'high'; n = [string]$n; output_format = 'png' }
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

# renvoie $true si la planche est generee, $false sinon (l'erreur est notee, on passe a la suivante)
function RunJob($job){
  $files = RefFiles $job
  $n = if ($job.n) { [int]$job.n } else { 3 }
  Write-Host ""
  Write-Host "=== $($job.id) : $($job.name) ($n variante(s)) ===" -ForegroundColor Cyan
  Write-Host ("references : " + (($files | ForEach-Object { Split-Path $_ -Leaf }) -join ', '))
  $model = 'gpt-image-2'; $fidelity = $true; $res = $null; $t0 = Get-Date
  for ($attempt = 1; $attempt -le 5; $attempt++) {
    $res = Send $job $files $n $model $fidelity
    if ($res.code -eq 200) { break }
    $short = if ($res.body.Length -gt 500) { $res.body.Substring(0, 500) } else { $res.body }
    if ($res.code -eq 400 -and $fidelity -and $res.body -match 'input_fidelity') { Write-Host "le modele refuse input_fidelity, nouvel essai sans"; $fidelity = $false; continue }
    if (($res.code -eq 400 -or $res.code -eq 404) -and $model -eq 'gpt-image-2' -and $res.body -match 'model') { Write-Host "gpt-image-2 indisponible, nouvel essai avec gpt-image-1"; $model = 'gpt-image-1'; continue }
    if (($res.code -eq 0 -or $res.code -eq 429 -or $res.code -ge 500) -and $attempt -lt 5) { Write-Host "erreur $($res.code), nouvel essai dans $(15*$attempt) s"; Start-Sleep -Seconds (15*$attempt); continue }
    Write-Host "ECHEC $($job.id) : HTTP $($res.code) : $short" -ForegroundColor Red
    Add-Content -LiteralPath 'output\erreurs.txt' -Value ("{0} {1} HTTP {2} : {3}" -f (Get-Date -Format s), $job.id, $res.code, $short)
    return $false
  }
  if ($res.code -ne 200) { Write-Host "ECHEC $($job.id) apres plusieurs essais" -ForegroundColor Red; return $false }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $m = [regex]::Matches($res.body, '"b64_json"\s*:\s*"([^"]+)"')
  if ($m.Count -eq 0) { Write-Host "ECHEC $($job.id) : reponse sans image" -ForegroundColor Red; return $false }
  $i = 0
  foreach ($x in $m) { $i++; $out = Join-Path $PSScriptRoot "output\$($job.id)_$($stamp)_v$i.png"; [IO.File]::WriteAllBytes($out, [Convert]::FromBase64String($x.Groups[1].Value.Replace('\/', '/'))); Write-Host "enregistre : output\$(Split-Path $out -Leaf)" -ForegroundColor Green }
  Write-Host ("fait en {0:N0} s avec {1}" -f ((Get-Date) - $t0).TotalSeconds, $model)
  return $true
}

$byId = @{}; foreach ($j in $jobs) { $byId[$j.id] = $j }
if (-not (Test-Path 'approved\charref.png')) { if (RunJob $byId['charref']) { exit 0 } else { exit 1 } }
if (-not (Test-Path 'approved\world.png')) { if (RunJob $byId['world']) { exit 0 } else { exit 1 } }

$todo = @($jobs | Where-Object { $_.batch -eq 1 -and -not (Get-ChildItem -LiteralPath 'output' -Filter "$($_.id)_*.png" -File -ErrorAction SilentlyContinue) -and (-not $_.uses -or -not (@($_.uses) | Where-Object { -not (Test-Path "approved\$_.png") })) })
if ($todo.Count -eq 0) { Write-Host "Rien a generer : toutes les planches ont deja leurs images."; exit 0 }
Write-Host ("{0} planche(s) a generer : {1}" -f $todo.Count, (($todo | ForEach-Object { $_.id }) -join ', '))
Write-Host "Compte une a trois minutes par planche. Tu peux laisser la fenetre ouverte et faire autre chose."
$ok = 0; $ko = 0
foreach ($j in $todo) { if (RunJob $j) { $ok++ } else { $ko++ } }
Write-Host ""
Write-Host ("Bilan : {0} planche(s) generee(s), {1} en echec." -f $ok, $ko)
if ($ko -gt 0) { exit 1 } else { exit 0 }
