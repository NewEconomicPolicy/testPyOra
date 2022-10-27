rem 
@set PYTHONPATH=D:\PyOraDev\testPyOra-main\BioModels;D:\PyOraDev\testPyOra-main\EnvModelModules;D:\PyOraDev\testPyOra-main\Constructor;D:\PyOraDev\testPyOra-main\LiveStock
@set initial_working_dir=%cd%
@chdir /D D:\PyORATOR\setup
rem start cmd.exe /k "D:\Python38\python.exe -W ignore D:\PyOraDev\testPyOra-main\InitInptsRslts\PyOratorGUI.py"
start cmd.exe /k "C:\Users\u07ad20\AppData\Local\Programs\Python\Python310\python.exe -W ignore D:\PyOraDev\testPyOra-main\InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%

