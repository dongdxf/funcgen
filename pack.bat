@echo off

cd bin
upx -9 funcgen.exe
cd ..

if exist funcgen.zip del /f funcgen.zip
rename bin funcgen
winrar a -afzip funcgen funcgen
rename funcgen bin
