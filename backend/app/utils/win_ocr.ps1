param([Parameter(Mandatory=$true)][string]$ImagePath)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
}[0]

Function AwaitOp($task, $type) {
    $m = $asTaskGeneric.MakeGenericMethod($type)
    $t = $m.Invoke($null, @($task))
    $t.Wait(-1) | Out-Null
    return $t.Result
}

[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.DataWriter, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null

if (-not (Test-Path $ImagePath)) {
    exit 0
}

$resolved = (Resolve-Path $ImagePath).Path
$bytes = [System.IO.File]::ReadAllBytes($resolved)
$stream = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
$writer = [Windows.Storage.Streams.DataWriter]::new($stream)
$writer.WriteBytes($bytes)
$null = AwaitOp ($writer.StoreAsync()) ([uint32])
$null = AwaitOp ($writer.FlushAsync()) ([bool])
$stream.Seek(0)

$decoder = AwaitOp ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = AwaitOp ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    $lang = [Windows.Globalization.Language]::new("en-US")
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
}

if ($null -eq $engine) {
    exit 0
}

$result = AwaitOp ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
if ($result -and $result.Text) {
    Write-Output $result.Text
}

