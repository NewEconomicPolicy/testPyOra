rem 
@set PYTHONPATH=D:\PyOraDevClone\testPyOra\BioModels;D:\PyOraDevClone\testPyOra\EnvModelModules;D:\PyOraDevClone\testPyOra\Constructor;D:\PyOraDevClone\testPyOra\LiveStock
@set initial_working_dir=%cd%
@chdir /D D:\PyOraDevClone\testPyOra\OratorRun\Docs\PyOrator_model_files\setup
rem start cmd.exe /k "D:\PyOraDevClone\testPyOra\InitInptsRslts\PyOratorGUI.py"
start cmd.exe /k "C:\Users\u07ad20\AppData\Local\Programs\Python\Python310\python.exe -W ignore D:\PyOraDevClone\testPyOra\InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%

