#!/bin/bash

# work in progress to make a bash script for macOS users (currently the .json file in the set up folder is problematic). Pythonpath needs to be corrected as well. 

export PYTHONPATH=../../../../BioModels/;../../../../EnvModelModules/;../../../../Constructor/;../../../../LiveStock/
# @set initial_working_dir=%cd%
cd /PyOraDevClone/testPyOra/OratorRun/Docs/PyOrator_model_files/setup/
# rem start cmd.exe /k "D:\PyOraDevClone\testPyOra\InitInptsRslts\PyOratorGUI.py"
python -W ignore ../../../../InitInptsRslts/PyOratorGUI.py
# @chdir /D %initial_working_dir%

