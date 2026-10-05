Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

pywPath = "C:\Users\TRADING_PRO\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
If fso.FileExists(pywPath) Then
    cmd = Chr(34) & pywPath & Chr(34) & " " & Chr(34) & scriptDir & "\main.pyw" & Chr(34)
Else
    cmd = "pythonw " & Chr(34) & scriptDir & "\main.pyw" & Chr(34)
End If

WshShell.Run cmd, 0, False
