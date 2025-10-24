param(
  [string]$Message = 'Parameter export unavailable. Please run the Python script with COMSOL mph to generate final_dimensions.json and profiles.'
)

# Placeholder error PNG only (no default files).
Add-Type -AssemblyName System.Drawing
$width = 1000; $height = 600
$bmp = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.Clear([System.Drawing.Color]::White)
$title = New-Object System.Drawing.Font ('Segoe UI', 28, [System.Drawing.FontStyle]::Bold)
$body  = New-Object System.Drawing.Font ('Segoe UI', 12, [System.Drawing.FontStyle]::Regular)
$red   = [System.Drawing.Brushes]::Crimson
$black = [System.Drawing.Brushes]::Black
$g.DrawString('ERROR', $title, $red, 420, 200)
$g.DrawString($Message, $body, $black, 100, 260)
$pngPath = Join-Path $PSScriptRoot 'geometry_profile.png'
$bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

Write-Host "Wrote placeholder $pngPath"

