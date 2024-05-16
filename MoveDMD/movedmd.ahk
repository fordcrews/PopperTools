; AutoHotkey Script to move DMD window up by xx pixels

; Enumerate all top-level windows and list their titles
WinGet, id, list,,, Program Manager
windowList := ""
Loop, %id%
{
    this_id := id%A_Index%
    WinGetTitle, title, ahk_id %this_id%
    WinGetClass, class, ahk_id %this_id%
    WinGetPos, X, Y, Width, Height, ahk_id %this_id%
    windowList .= "ID: " . this_id . " | Title: " . title . " | Class: " . class . " | Position: " . X . "," . Y . " | Size: " . Width . "x" . Height . "`n"
}

; Display the list of windows
;MsgBox, %windowList%


;Pause


DmdTitle := "Virtual DMD" ; You can update this after finding the correct window

; Detect the DMD window and get its current position
IfWinExist, %DmdTitle%
{
    ; Get the current position and size of the DMD window
    WinGetPos, X, Y, Width, Height, %DmdTitle%

    ; Move the DMD window up by 20 pixels
    Y := Y + 260
    WinMove, %DmdTitle%, , X, Y

    ; Confirm the action
   ; MsgBox, Moved DMD window up by 20 pixels.
   
   ; Activate the DMD window
    WinActivate, %DmdTitle%

    ; Get the new position of the DMD window
    Sleep, 500 ; Wait for the window to settle
    WinGetPos, NewX, NewY, , , %DmdTitle%

 MsgBox, Window XY %X% %Y% NewXY %NewX% %NewY%.

    ; Move the mouse to the new position of the DMD window
    MouseMove, NewX - 5, NewY + 5 ; Adjust the offset as needed

    ; Right-click to open the context menu
    Click, Right

    ; Send the keystroke to save the position
 ;   Sleep, 500 ; Wait for the context menu to appear
   
}
else
{
    MsgBox, DMD window not found.
}
