#!/bin/bash

#of12 # actuvate openfoam12 if not yet on    
source /opt/openfoam12/etc/bashrc
# Source tutorial run functions
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"

# runApplication => executes the command and the log is sent to log.[appName]
# run parallel => executes the command in parallel (like mpirun -np ...) and log is sent to log.[appName]
# Both work such that whenever the log.appname already exists => the app execution is skipped

runApplication blockMesh
runApplication surfaceFeatures 

runApplication decomposePar

runParallel snappyHexMesh

runApplication reconstructPar



