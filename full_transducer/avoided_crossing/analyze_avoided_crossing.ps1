param(
  [string]$CsvPath = 'avoided_crossing_data.csv',
  [string]$OutPng = 'avoided_crossing.png'
)

# Load CSV
$data = Import-Csv -Path (Join-Path $PSScriptRoot $CsvPath)
if (-not $data) { Write-Error "No data found in $CsvPath"; exit 1 }

# Extract arrays
$periods = @()
$em = @()
$om = @()
foreach ($row in $data) {
  $periods += [double]$row.'Transducer Period (in nm)'
  $em += [double]$row.'Electromechanical Mode (in GHz)'
  $om += [double]$row.'Optomechanical Mode (in GHz)'
}

# Compute min splitting
$minIdx = 0
$minSplit = [double]::PositiveInfinity
for ($i=0; $i -lt $periods.Count; $i++) {
  $s = [math]::Abs($em[$i] - $om[$i])
  if ($s -lt $minSplit) { $minSplit = $s; $minIdx = $i }
}
$minPeriod = $periods[$minIdx]
$gMHz = ($minSplit * 1000.0) / 2.0

# Drawing with System.Drawing
Add-Type -AssemblyName System.Drawing
$width = 1000; $height = 600
$bmp = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$white = [System.Drawing.Color]::White
$g.Clear($white)

# Margins and plot area
$left = 80; $right = 40; $top = 40; $bottom = 70
$plotW = $width - $left - $right
$plotH = $height - $top - $bottom

# Determine ranges
$minP = ($periods | Measure-Object -Minimum).Minimum
$maxP = ($periods | Measure-Object -Maximum).Maximum
$allF = @()
for ($i=0; $i -lt $em.Count; $i++) { $allF += $em[$i]; $allF += $om[$i] }
$minF = ($allF | Measure-Object -Minimum).Minimum
$maxF = ($allF | Measure-Object -Maximum).Maximum
$padF = 0.005
$minF -= $padF; $maxF += $padF

function MapX($p, $minP, $maxP, $left, $plotW){ if (($maxP - $minP) -eq 0) { return $left } return $left + ($p - $minP) * $plotW / ($maxP - $minP) }
function MapY($f, $minF, $maxF, $top, $plotH){ if (($maxF - $minF) -eq 0) { return $top + $plotH/2 } return $top + ($maxF - $f) * $plotH / ($maxF - $minF) }

# Axes
$blackPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Black), 1
$g.DrawRectangle($blackPen, $left, $top, $plotW, $plotH)

# Grid lines (5 x 5)
$gridPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(40,0,0,0)), 1
for ($i=1; $i -lt 5; $i++){
  $x = $left + $plotW * $i / 5.0
  $g.DrawLine($gridPen, $x, $top, $x, $top + $plotH)
  $y = $top + $plotH * $i / 5.0
  $g.DrawLine($gridPen, $left, $y, $left + $plotW, $y)
}

# Fonts
$font = New-Object System.Drawing.Font 'Segoe UI', 11
$small = New-Object System.Drawing.Font 'Segoe UI', 9
$redPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Red), 2
$bluePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Blue), 2
$ptRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Red)
$ptBlue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Blue)

# Plot series
for ($i=0; $i -lt $periods.Count-1; $i++){
  $x1 = MapX $periods[$i] $minP $maxP $left $plotW
  $y1a = MapY $em[$i] $minF $maxF $top $plotH
  $y1b = MapY $om[$i] $minF $maxF $top $plotH
  $x2 = MapX $periods[$i+1] $minP $maxP $left $plotW
  $y2a = MapY $em[$i+1] $minF $maxF $top $plotH
  $y2b = MapY $om[$i+1] $minF $maxF $top $plotH
  $g.DrawLine($redPen, $x1, $y1a, $x2, $y2a)
  $g.DrawLine($bluePen, $x1, $y1b, $x2, $y2b)
}
# Points
for ($i=0; $i -lt $periods.Count; $i++){
  $x = MapX $periods[$i] $minP $maxP $left $plotW
  $yA = MapY $em[$i] $minF $maxF $top $plotH
  $yB = MapY $om[$i] $minF $maxF $top $plotH
  $g.FillEllipse($ptRed, $x-3, $yA-3, 6, 6)
  $g.FillEllipse($ptBlue, $x-3, $yB-3, 6, 6)
}

# Labels
$title = 'Avoided Crossing Analysis'
$g.DrawString($title, $font, [System.Drawing.Brushes]::Black, $left, 8)
$g.DrawString('Transducer Period (nm)', $font, [System.Drawing.Brushes]::Black, $left + $plotW/2 - 100, $top + $plotH + 30)
$g.DrawString('Frequency (GHz)', $font, [System.Drawing.Brushes]::Black, 5, $top + $plotH/2 - 10)

# Legend
$legendX = $left + $plotW - 210
$legendY = $top + 10
$legendW = 200
$legendH = 40
$g.FillRectangle([System.Drawing.Brushes]::White, $legendX, $legendY, $legendW, $legendH)
$g.DrawRectangle($blackPen, $legendX, $legendY, $legendW, $legendH)
$g.DrawLine($redPen, $legendX + 10, $legendY + 15, $legendX + 40, $legendY + 15)
$g.DrawString('Electromechanical', $small, [System.Drawing.Brushes]::Black, $legendX + 45, $legendY + 7)
$g.DrawLine($bluePen, $legendX + 10, $legendY + 30, $legendX + 40, $legendY + 30)
$g.DrawString('Optomechanical', $small, [System.Drawing.Brushes]::Black, $legendX + 45, $legendY + 22)

# Annotate min splitting
$xMin = MapX $minPeriod $minP $maxP $left $plotW
$yA = MapY $em[$minIdx] $minF $maxF $top $plotH
$yB = MapY $om[$minIdx] $minF $maxF $top $plotH
$dashPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Black), 1
$dashPen.DashStyle = 'Dash'
$g.DrawLine($dashPen, $xMin, $yA, $xMin, $yB)
$midY = ($yA + $yB) / 2

# Place the splitting annotation just below the legend to avoid blocking the graph
$txt = [string]::Format("min Delta f ~ {0:F3} MHz (g ~ {1:F3} MHz) at {2} nm", $minSplit*1000.0, $gMHz, [int]$minPeriod)
$textW = 320.0
$textH = 40.0
$annX = [Math]::Max($left, [Math]::Min($left + $plotW - $textW, $legendX + $legendW/2.0 - $textW/2.0))
$annY = [Math]::Max($top, [Math]::Min($top + $plotH - $textH, $legendY + $legendH + 6))
$g.DrawString($txt, $small, [System.Drawing.Brushes]::Black, [System.Drawing.RectangleF]::new([single]$annX, [single]$annY, [single]$textW, [single]$textH))

# Save PNG
$outPath = Join-Path $PSScriptRoot $OutPng
$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Wrote $outPath"
