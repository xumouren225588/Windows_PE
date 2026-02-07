On Error Resume Next
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set drive = wmi.Get("Win32_DiskDrive.DeviceID='\\.\PHYSICALDRIVE0'")
If Err.Number <> 0 Then
    Msgbox Err.Description
    WScript.Quit 1
End If
If drive.InterfaceType = "IDE" Or drive.InterfaceType = "SCSI" Then
    WScript.Quit 0
Else
    MsgBox "Assertion failed."
    WScript.Quit 1
End If
