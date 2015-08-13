import pexpect
import subprocess
import os
import time
import collections
import numpy as np 
import fnmatch
import pickle
from copy import deepcopy
import itertools
from subprocess import call        
import multiprocessing as mp
import progressbar
import concurrent.futures


home = os.path.expanduser("~")
bngExecutable = os.path.join(home, 'workspace', 'bionetgen', 'bng2', 'BNG2.pl')


def setBngExecutable(executable):
    bngExecutable = executable


def getBngExecutable():
    return bngExecutable




def getValidFiles(directory, extension):
    """
    Gets a list of bngl files  in a given 'directory'
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*.{0}'.format(extension)):
            matches.append(os.path.join(root, filename))
    return matches

def simulateMethod(bngconsole, method, simulationTime):
    """
    time and execute the BNG simulate method corresponding to parameter 'method' and 'simulationTime'
    """
    simulateParameters = ['method=>"{0}"'.format(method[0]), 't_end=>"{0}"'.format(simulationTime)]
    if method[1] != '':
        simulateParameters.append(method[1])
    simulateParameters = ', '.join(simulateParameters)
    print 'action simulate({{{0}}})'.format(simulateParameters)
    bngconsole.sendline('action simulate({{{0}}})'.format(simulateParameters))
    bngconsole.expect('BNG>')
    print '_'.join(method)
    simulationTime = float(bngconsole.before.split('\n')[-2].split(' ')[-2])
    print simulationTime
    bngconsole.sendline('resetConcentrations()')
    bngconsole.expect('BNG>')
    return float(bngconsole.before.split('\n')[-2].split(' ')[-2])
    

def bnglsimulate(bnglFile, methodList, simulationTime, repetitions, timeout=600):
    """
    perform an execution of model located in file 'bnglFile' using methods in methodList
    """
    timings = {}

    timings[bnglFile] = {}
    for method in methodList:
        timings[bnglFile]['_'.join(method)] = []



    try:
        bngconsole = pexpect.spawn('{0} --console'.format(getBngExecutable()), timeout=timeout)
        bngconsole.expect('BNG>')
        print '\tloading file...'
        bngconsole.sendline('load {0}'.format(bnglFile))
        bngconsole.expect('BNG>')
        print '\tgenerating network...'
        bngconsole.sendline('action generate_network()')
        bngconsole.expect('BNG>')

        print '\tsimulating...'
        for method in methodList:
            print('\t{0} analysis'.format(method))
            for _ in range(0, repetitions):
                #simulate function
                simulateParameters = ['method=>"{0}"'.format(method[0]), 't_end=>"{0}"'.format(simulationTime)]
                if method[1] != '':
                    simulateParameters.append(method[1])
                simulateParameters = ', '.join(simulateParameters)
                print 'action simulate({{{0}}})'.format(simulateParameters)
                bngconsole.sendline('action simulate({{{0}}})'.format(simulateParameters))
                bngconsole.expect('BNG>')
                print '_'.join(method)
                simulationTime = float(bngconsole.before.split('\n')[-2].split(' ')[-2])
                print simulationTime
                bngconsole.sendline('resetConcentrations()')
                bngconsole.expect('BNG>')

                
                timings[bnglFile]['_'.join(method)].append(simulationTime)
        bngconsole.close()
    except pexpect.TIMEOUT:
        bngconsole.kill(0)
    return timings

def dummy(result,output):
    pass

def mergeTimmings(timmings, finalDictionary):
    for fileName in timmings:
        for method in timmings[fileName]:
            finalDictionary[fileName][method].extend(timmings[fileName][method])

def parallelHandling(simulationSetup, repetitions, function, outputDir, options = [], postExecutionFunction=dummy):
    futures = []
    workers = mp.cpu_count() - 1
    i = 0
    print 'running in {0} cores'.format(workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for _ in range(repetitions):
            #function(simulationSetup[0],[simulationSetup[1]], 40, repetitions / workers)
            print function,simulationSetup,repetitions/workers
            futures.append(executor.submit(function, simulationSetup[0], [simulationSetup[1]], 40, repetitions / workers))
        for future in concurrent.futures.as_completed(futures, timeout=3600):
            print 'prepost'
            print future.result()
            print 'postpost'
            postExecutionFunction(future.result(), outputDir)



def main():
    # select folder where bngl files are located
    bnglfiles = getValidFiles(os.path.join(home, 'workspace', 'bionetgen', 'bng2', 'Models2'), 'bngl')
    #bnglfiles = getValidFiles(os.path.join(home, 'workspace', 'bionetgen', 'parsers','SBMLparser','curated'), 'bngl')
    #bnglfiles = getValidFiles(os.path.join('.', 'bnglTest'), 'bngl')

    plaOptions = [['fEuler', 'midpt', 'rk4'], ['pre-neg:sb', 'Anderson:sb', 'pre-eps:sb'], ['0.01','0.03','0.05']]
    plaOptions = list(itertools.product(*plaOptions))
    simulationMethods = [['pla', 'pla_config=>' + '|'.join(x)] for x in plaOptions]
    simulationMethods.append(['ode', ''])

    fileName = ['bnglTest/egfr_net.bngl']
    fileNameOptionsTemp = [fileName, simulationMethods]
    simulationSetup = list(itertools.product(*fileNameOptionsTemp))
    
    print simulationSetup
    '''
    for idx, bngl in enumerate(simulationSetup[0:3]):
        print('Processing {1}/{2}= {0}'.format(bngl, idx, len(bnglfiles)))
        try:
            bnglsimulate(bngl, simulationMethods, '1', 1)
        except pexpect.EOF:
            print 'error processing {0}'.format(bngl)
            continue
    '''
    tempResults = collections.defaultdict(lambda: collections.defaultdict(list))
    parallelHandling(simulationSetup[-1], 3, bnglsimulate, tempResults,postExecutionFunction=mergeTimmings)
    print tempResults

    """
    # file to store timings in. It will be stored as a dictionary of values. These can be sent to a pandas dataframe using
    # pandas.DataFrame.from_dict(<dict>)
    with open('results3.dump', 'wb') as f:
        pickle.dump(dict(timings2), f)
    """

if __name__ == "__main__":
    main()
