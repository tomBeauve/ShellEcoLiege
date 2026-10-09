#!/bin/bash
# ==========================================
# PART 1: SLURM DIRECTIVES (Resource Requests)
# ==========================================
#SBATCH --job-name=FWBase-0-5                 # Name of your job in the queue
#SBATCH --output=slurm-%j.out            # Standard output log (%j = job ID)
#SBATCH --error=slurm-%j.err             # Error log file
#SBATCH --nodes=1                        # Number of physical compute nodes
#SBATCH --ntasks-per-node=32             # Number of CPU cores (tasks) to use
#SBATCH --time=12:00:00                  # Maximum run time (HH:MM:SS) - job stops if exceeded
#SBATCH --mem=40G                       # Total RAM requested for the node

# ==========================================
# PART 2: ENVIRONMENT SETUP
# ==========================================

# Load required software module (e.g., OpenFOAM or STAR-CCM+)
module load releases/2023b
module load OpenFOAM/12-foss-2023b
source $FOAM_BASH


CASE_PATH="FormulaStudent/BaseDesign/Mesh128"

mkdir -p $SCRATCH/$CASE_PATH
cp -r $HOME/$CASE_PATH/. $SCRATCH/$CASE_PATH/

cd $SCRATCH/$CASE_PATH

# ==========================================
# PART 3: EXECUTION COMMANDS
# ==========================================
mkdir -p log


blockMesh > log/log.blockMesh 2>&1
surfaceFeatures > log/log.surfaceFeatures 2>&1

decomposePar -force > log/log.decomposeParMesh 2>&1

srun -n $SLURM_NTASKS snappyHexMesh -parallel -overwrite > log/log.snappyHexMesh 2>&1
srun -n $SLURM_NTASKS snappyHexMesh -dict system/snappyHexMeshDict_layer -parallel -overwrite > log/log.snappyHexMeshLayer 2>&1

reconstructPar -constant > log/log.reconstructParMesh 2>&1
rm -rf processor*
decomposePar -force > log/log.decomposeParSolver 2>&1

srun -n $SLURM_NTASKS renumberMesh -overwrite > log/log.renumberMesh 2>&1

srun mapFields ../coarse -consistent -parallelTarget -sourceTime latestTime

srun -n $SLURM_NTASKS foamRun -parallel > log/log.simpleFoam 2>&1

srun -n $SLURM_NTASKS foamPostProcess -solver incompressibleFluid -noZero > log/log.foamPostProcess 2>&1

reconstructPar > log/log.reconstructParResults 2>&1

rm -rf processor*

cp -r $SCRATCH/FWBase/log/log.foamRun /home/ulg/mtfc/tbeauve/FWBase/log