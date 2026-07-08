Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
workDir = fso.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = workDir

ws.Run "powershell -NoProfile -Command Get-CimInstance Win32_Process -Filter 'Name=''python.exe''' | Where-Object { $_.CommandLine -match 'mock_server\.py|run\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }", 0, True
ws.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr "":3000.*LISTENING""') do taskkill /f /pid %a >nul 2>&1", 0, True
WScript.Sleep 2000

ws.Run "powershell -NoProfile -Command Start-Process -FilePath 'py' -ArgumentList '-3.8','mock_server.py' -WorkingDirectory '" & workDir & "' -WindowStyle Minimized", 0, False

For i = 1 To 15
    WScript.Sleep 1000
    ret = ws.Run("powershell -NoProfile -Command try { Invoke-WebRequest 'http://127.0.0.1:3000/' -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }", 0, True)
    If ret = 0 Then Exit For
Next

ws.Run "powershell -NoProfile -Command Start-Process -FilePath 'py' -ArgumentList '-3.8','run.py' -WorkingDirectory '" & workDir & "'", 0, False