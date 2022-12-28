rem
@set root_dir=G:\PyOraDev\testPyOra\
@set PYTHONPATH=%root_dir%InitInptsRslts;%root_dir%Constructor;%root_dir%BioModels;%root_dir%EnvModelModules;%root_dir%LiveStock
@set initial_working_dir=%cd%
@chdir /D E:\ORATOR\setup
start cmd.exe /k "E:\Python38\python.exe -W ignore %root_dir%InitInptsRslts\PyOratorGUI.py"
@chdir /D %initial_working_dir%
