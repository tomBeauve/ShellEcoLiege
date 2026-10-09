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

runParallel snappyHexMesh -overwrite

#mv log.snappyHexMesh log.snappyHexMesh1
#runParallel snappyHexMesh -overwrite -dict system/snappyHexMeshDict_layer


runApplication reconstructPar


rm -rf processor*
rm log.decomposePar
rm log.reconstructPar
runApplication decomposePar
runParallel renumberMesh -overwrite
runParallel checkMesh


#runApplication mapFields ../meshNew1 -consistent -parallelSource -parallelTarget -sourceTime latestTime
runParallel foamRun # &


runParallel foamPostProcess -solver incompressibleFluid -noZero

runApplication reconstructPar

# rm -rf processor*

