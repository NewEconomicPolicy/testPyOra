rem
@set root_dir=D:\testPyOra\
@set PYTHONPATH=%root_dir%InitInptsRslts;%root_dir%Constructor;%root_dir%BioModels;%root_dir%EnvModelModules;%root_dir%LiveStock
@set initial_working_dir=%cd%
@chdir /D D:\testPyOra\OratorRun\Docs\PyOrator_model_files\setup
start cmd.exe /k "C:\Users\u07ad20\AppData\Local\Programs\Python\Python310\python.exe -W ignore %root_dir%InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%
