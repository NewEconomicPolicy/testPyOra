rem 
@set PYTHONPATH=D:\testPyOra\BioModels;D:\testPyOra\EnvModelModules;D:\testPyOra\Constructor;D:\testPyOra\LiveStock
@set initial_working_dir=%cd%
@chdir /D D:\testPyOra\OratorRun\Docs\PyOrator_model_files\setup
rem start cmd.exe /k "D:\testPyOra\InitInptsRslts\PyOratorGUI.py"

rem file below needs to obscure C:/ path that contains my personal information (look into this soon!)
rem also find out more about how double backslashes work. terminology a bit complicated for me brain atm...
start cmd.exe /k "C:\Users\u07ad20\AppData\Local\Programs\Python\Python310\python.exe -W ignore D:\testPyOra\InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%

