Option Explicit
Dim shell, fso, folder, runtime, pythonw, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
runtime = fso.BuildPath(folder, "runtime")
shell.CurrentDirectory = runtime
pythonw = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\miniconda3\pythonw.exe"
If Not fso.FileExists(pythonw) Then pythonw = "pythonw.exe"
On Error Resume Next
result = shell.Run(Chr(34) & pythonw & Chr(34) & " -m veran_advisor.demo", 0, False)
If Err.Number <> 0 Then
  MsgBox "Unable to start. Please use the .cmd launcher or check Python installation.", 48, "VERAN"
End If
