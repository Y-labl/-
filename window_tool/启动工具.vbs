Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
workDir = fso.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = workDir
ws.Run "powershell -NoProfile -Command Get-CimInstance Win32_Process -Filter 'Name=''python.exe''' | Where-Object { $_.CommandLine -match 'main\.py' -and $_.CommandLine -notmatch 'mock_server|stoneclient' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }", 0, True
WScript.Sleep 1000
ws.Run "powershell -NoProfile -Command Start-Process -FilePath 'py' -ArgumentList '-3.8','main.py' -WorkingDirectory '" & workDir & "' -WindowStyle Minimized", 0, False