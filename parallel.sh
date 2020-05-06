#!/bin/sh

# Set the number of nodes and processes per node
#PBS -l nodes=1:ppn=6

# Set max wallclock time
#PBS -l walltime=48:00:00

# Set maximum memory
#PBS -l mem=64gb

# Set name of job
#PBS -N  costdata 

# Use submission environment
#PBS -V
cd ~/work/GETP 
source ~/python3.6/bin/activate
python3 benders_repn.py 
