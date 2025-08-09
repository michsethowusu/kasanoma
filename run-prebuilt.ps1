Param(
  [string]$Image = "kasanoma-piper:latest",
  [int]$Port = 8000,
  [string]$ImageTar = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModelDir = Join-Path $ScriptDir "model"
if (-not (Test-Path $ModelDir)) {
  Write-Error "Model directory not found at $ModelDir. Expected model.onnx and config.json"
  exit 1
}

if (-not (docker image inspect $Image 2>$null)) {
  if (-not $ImageTar -or -not (Test-Path $ImageTar)) {
    $DefaultTar = Join-Path $ScriptDir "images/kasanoma-piper.tar"
    if (Test-Path $DefaultTar) { $ImageTar = $DefaultTar }
  }
  if ($ImageTar -and (Test-Path $ImageTar)) {
    Write-Host "Loading Docker image from $ImageTar ..."
    docker load -i $ImageTar | Out-Null
  } else {
    Write-Error "Docker image '$Image' not found locally and no tarball provided."
    Write-Host "Provide a local image tar via -ImageTar or at images/kasanoma-piper.tar"
    Write-Host "Expected tag: $Image"
    exit 1
  }
}

Write-Host "Running $Image on http://localhost:$Port"
docker run --rm -p "$Port:8000" -v "$ModelDir:/data/model" $Image
