#!/bin/sh

# Set the number of nodes and processes per node
#PBS -l nodes=1:ppn=1

# Set max wallclock time
#PBS -l walltime=188:00:00

# Set maximum memory
#PBS -l mem=100gb

# Set name of job
#PBS -N repn 

# Use submission environment
#PBS -V
cd ~/work/GETP 
export PATH=$PATH:/opt/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux
source ~/python3.6/bin/activate
/home/canl1/python3.6/bin/python  benders_repn.py
