#!/bin/bash
mkdir /home/joakim/work/horse/jsons
conda create --name pyhton3 python=3.5
activate python3
conda install numpy -y
conda install psycopg2 -y
conda install -c conda-forge mechanicalsoup=0.6.0 -y
