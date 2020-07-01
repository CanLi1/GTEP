#!/bin/sh

# Set the number of nodes and processes per node
#PBS -l nodes=1:ppn=1

# Set max wallclock time
#PBS -l walltime=48:00:00

# Set maximum memory
#PBS -l mem=64gb

# Set name of job
#PBS -N  repn_day 

# Use submission environment
#PBS -V
cd ~/work/GETP 
source ~/python3.6/bin/activate
export PATH=$PATH:/opt/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux
python3 repn_day.py
