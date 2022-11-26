import random
import subprocess
import os
import re
import csv
import time
import shutil
import multiprocessing
from tqdm import tqdm


DATA_SUITES = (
    'uf20-71R',
    'uf20-81R',
    'uf20-91R',
    'uf50-218R',
    'uf75-325',
    'ruf20-91R',
    'ruf50-218R',
    'ruf75-320R',
    '5uf20-420',
    '5uf50-1050',
    '7uf20-1760',
)

DATA_DIRECTORY = 'data'
OUTPUT_DIRECTORY = 'output'
BACKUP_DIRECTORY = 'backup'

RUNS = 1000


def flatten(list):
    return [item for sublist in list for item in sublist]


def gsat(datafile, cmd='gsat2', p=0.4, i=500, T=1):
    process = subprocess.run([
        cmd,
        '-r', random.randint(1, 1_000_000).__str__(),
        '-p', p.__str__(),
        '-i', i.__str__(),
        '-T', T.__str__(),
        datafile
    ], capture_output=True)
    stderr = process.stderr.decode()
    iterations_count, max_iterations_count, fulfilled_clauses_count, clauses_count = stderr.strip().split(' ')
    satisfiable = fulfilled_clauses_count == clauses_count
    return datafile, int(iterations_count), satisfiable


def probsat(datafile, cmd='/home/zapotlub/probSAT/probSAT', fct=0, cb=2.3, maxflips=500, runs=1):
    process = subprocess.run([
        cmd,
        '--fct', fct.__str__(),
        '--cb', cb.__str__(),
        '--runs', runs.__str__(),
        '--maxflips', maxflips.__str__(),
        datafile,
        random.randint(1, 1_000_000).__str__()
    ], capture_output=True)
    stdout = process.stdout.decode()
    flip_count = re.search(r'numFlips +: (\d+)', stdout).group(1)
    satisfiable = re.search(r'SATISFIABLE', stdout) is not None
    return datafile, int(flip_count), satisfiable


if __name__ == '__main__':
    if not os.path.exists(BACKUP_DIRECTORY):
        os.mkdir(BACKUP_DIRECTORY)
    BACKUP_TIMESTAMP = time.time().__str__()

    if os.path.exists(OUTPUT_DIRECTORY):
        shutil.copytree(OUTPUT_DIRECTORY, os.path.join(BACKUP_DIRECTORY, BACKUP_TIMESTAMP))

    shutil.rmtree(OUTPUT_DIRECTORY)
    os.mkdir(OUTPUT_DIRECTORY)

    for suite in DATA_SUITES:
        print(suite)

        os.mkdir(os.path.join(OUTPUT_DIRECTORY, suite))
        gsat_output = open(os.path.join(OUTPUT_DIRECTORY, suite, 'gsat.csv'), 'w')
        probsat_output = open(os.path.join(OUTPUT_DIRECTORY, suite, 'probsat.csv'), 'w')

        gsat_writer = csv.writer(gsat_output)
        probsat_writer = csv.writer(probsat_output)

        gsat_heading = ['instance', 'iterations', 'success']
        probsat_heading = ['instance', 'flips', 'success']

        gsat_writer.writerow(gsat_heading)
        probsat_writer.writerow(probsat_heading)

        for root, _, files in os.walk(os.path.join(DATA_DIRECTORY, suite)):
            run_files = flatten([[os.path.join(root, file)] * RUNS for file in files])
            pool = multiprocessing.Pool(processes=8)

            gsat_results = list(tqdm(pool.imap(gsat, run_files), total=len(run_files)))
            probsat_results = list(tqdm(pool.imap(probsat, run_files), total=len(run_files)))

            gsat_results = [(result[0].split('/')[-1], result[1], result[2]) for result in gsat_results]
            probsat_results = [(result[0].split('/')[-1], result[1], result[2]) for result in probsat_results]

            gsat_results.sort(key=lambda result: result[0])
            probsat_results.sort(key=lambda result: result[0])

            gsat_writer.writerows(gsat_results)
            probsat_writer.writerows(probsat_results)
