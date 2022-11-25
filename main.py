import random
import subprocess
import os
import re
import csv
import time
import shutil

DATA_DIRECTORY = 'data'

DATA_SUITES = (
    # 'uf20-71R',
    # 'uf20-81R',
    # 'uf20-91R',
    # 'uf50-218R',
    'uf75-325',
    # 'ruf20-91R',
    # 'ruf50-218R',
    # 'ruf75-320R',
    # '5uf20-420',
    # '5uf20-1050',
    # '7uf20-1760',
)

OUTPUT_DIRECTORY = 'output'
BACKUP_DIRECTORY = 'backup'

RUNS = 100


# ------------------------


def gsat(datafile, cmd='gsat2', p=0.4, i=15000, T=50):
    process = subprocess.run([
        cmd, '-r', random.randint(1, 1_000_000).__str__(), '-p', p.__str__(), '-i', i.__str__(), '-T', T.__str__(), datafile],
        capture_output=True)
    stderr = process.stderr.decode()
    iterations_count, max_iterations_count, fulfilled_clauses_count, clauses_count = stderr.strip().split(' ')
    satisfiable = fulfilled_clauses_count == clauses_count
    if not satisfiable:
        raise Exception("gsat not satisfiable clause", fulfilled_clauses_count, clauses_count)
    # print('g', iterations_count, satisfiable)
    return int(iterations_count), satisfiable


def probsat(datafile, cmd='/home/zapotlub/probSAT/probSAT', ca=0, cb=2.3, runs=500, maxflips=500):
    process = subprocess.run([
        cmd,
        '--fct', ca.__str__(), '--cb', cb.__str__(),
        '--runs', runs.__str__(), '--maxflips', maxflips.__str__(), datafile, random.randint(1, 1_000_000).__str__()],
        capture_output=True)
    stdout = process.stdout.decode()
    flip_count = re.search(r'numFlips +: (\d+)', stdout).group(1)
    satisfiable = re.search(r'SATISFIABLE', stdout) is not None
    if not satisfiable:
        raise Exception("probsat not satisfiable clause")
    # print('p', flip_count, satisfiable)
    return int(flip_count), satisfiable


# Press the green button in the gutter to run the script.
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

        gsat_heading = ['file']
        for i in range(RUNS):
            gsat_heading.append('gsat_run_' + i.__str__())

        probsat_heading = ['file']
        for i in range(RUNS):
            probsat_heading.append('probsat_run_' + i.__str__())

        gsat_writer.writerow(gsat_heading)
        probsat_writer.writerow(probsat_heading)

        for root, _, files in os.walk(os.path.join(DATA_DIRECTORY, suite)):
            for file in files:
                if file.endswith(".cnf"):
                    print('- ', file.ljust(15), end=" ", flush=True)

                    filepath = os.path.join(root, file)

                    gsat_iterations = []
                    probsat_flips = []
                    print('\tG:', end=" ")

                    for i in range(RUNS):
                        if (i + 1) % (RUNS / 4) == 0:
                            print(f'{int((RUNS / 100) * (i + 1))}%', end=" ", flush=True)
                        iterations_count, _ = gsat(filepath)
                        gsat_iterations.append(iterations_count.__str__())

                    print('\tP:', end=" ")
                    for i in range(RUNS):
                        if (i + 1) % (RUNS / 4) == 0:
                            print(f'{int((RUNS / 100) * (i + 1))}%', end=" ", flush=True)
                        flip_count, _ = probsat(filepath)
                        probsat_flips.append(flip_count.__str__())

                    print()
                    # print(file, gsat_iterations, probsat_flips)
                    gsat_writer.writerow([file] + gsat_iterations)
                    probsat_writer.writerow([file] + probsat_flips)
