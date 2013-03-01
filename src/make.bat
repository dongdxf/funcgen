@echo off

rmdir /S /Q ..\bin

mkdir ..\bin
xcopy README    ..\bin\
xcopy config    ..\bin\config\    /E
xcopy doc       ..\bin\doc\       /E
xcopy history   ..\bin\history\   /E
xcopy input     ..\bin\input\     /E
xcopy log       ..\bin\log\       /E
xcopy output    ..\bin\output\    /E
xcopy templates ..\bin\templates\ /E

cxfreeze funcgen.py --target-dir ..\bin --base-name=win32gui
