rem 
@set PYTHONPATH=G:\PyOraDev\testPyOra\BioModels;G:\PyOraDev\testPyOra\EnvModelModules
@set initial_working_dir=%cd%
@chdir /D G:\PyOraDev\testPyOra\OratorRun\setup
start cmd.exe /k "E:\Python38\python.exe -W ignore G:\PyOraDev\testPyOra\InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%
