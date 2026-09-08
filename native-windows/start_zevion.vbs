' Zevion — Silent Launcher (no terminal, no flash)
' Double-click this file to open the Zevion GUI launcher directly.
' Uses pythonw so NO console window ever appears.

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
launcherPath = scriptDir & "\launcher.pyw"

' Run with pythonw (no console). WindowStyle 1 = normal, focused.
objShell.Run "pythonw """ & launcherPath & """", 1, False
