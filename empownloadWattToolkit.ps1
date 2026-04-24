$ie = New-Object -ComObject InternetExplorer.Application
$ie.Visible = $false
$ie.Navigate('https://wwn.lanzouy.com/iGGCM3kdvohe')
while ($ie.Busy -or $ie.ReadyState -ne 4) { Start-Sleep -Milliseconds 100 }
$iframe = $ie.Document.getElementsByTagName('iframe') | Where-Object {$_.name -eq '1777037270'}
if ($iframe) {
    $iframeUrl = $iframe.src
    $ie.Navigate($iframeUrl)
    while ($ie.Busy -or $ie.ReadyState -ne 4) { Start-Sleep -Milliseconds 100 }
    $downloadLink = $ie.Document.getElementsByTagName('a') | Where-Object {$_.innerText -like '*涓嬭浇*'}
    if ($downloadLink) {
        $downloadUrl = $downloadLink.href
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($downloadUrl, 'D:\Temp\WattToolkit.Installer.exe')
        $webClient.Dispose()
        Write-Host 'Download completed!'
    } else {
        Write-Host 'Download link not found'
    }
} else {
    Write-Host 'Iframe not found'
}
$ie.Quit()
