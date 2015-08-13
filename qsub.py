#!/usr/bin/python
# Example PBS cluster job submission in Python

from popen2 import popen2
import time
    
# If you want to be emailed by the system, include these in job_string:
#PBS -M your_email@address
#PBS -m abe  # (a = abort, b = begin, e = end)

# Loop over your jobs
import os.path
import fnmatch
import argparse
import re
import itertools

def getFiles(directory,extension):
    """
    Gets a list of bngl files that could be correctly translated in a given 'directory'

    Keyword arguments:
    directory -- The directory we will recurseviley get files from
    extension -- A file extension filter
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*.{0}'.format(extension)):
            filepath = os.path.abspath(os.path.join(root, filename))
            matches.append([filepath, os.path.getsize(os.path.join(root, filename))])

    #sort by size
    #matches.sort(key=lambda filename: filename[1], reverse=False)
    
    matches = [x[0] for x in matches]

    return matches

queue_list= {'noc_64_core':64, 'serial_queue':1, 'dept_24_core':24, 'dmz_core36':36,'bahar_64_core':64,'bahar_12_core':12}
import progressbar
import tempfile
import yaml
def start_queue(simulationSetup, repetitions, outputdirectory, queue, noOfBatches, nodes=1):
    """
    sends a batch job with the qsub queue and executes a command over it.
    using PBS commands
 
    Keyword arguments:
    fileNameSet -- A list of files containg the files to be sent to the queue
    outputdirectory -- The directory we will finally place our results in
    queue -- The queue we will send the job to. It has to make reference to an entry in queue_list
    batchsize -- The total number of jobs per batch job. (in other words, the number of nodes we will be using is <fileNameSet>/<batchSize>. Typically you want this to be a multiple of the number of cores per node.)
    """
    progress = progressbar.ProgressBar()
    settings = 'settings.yaml'
    for idx in progress(range(0,len(simulationSetup))):
        #fileNameSubset = fileNameSet[idx:min(idx+batchSize,len(fileNameSet))]
        settings = {}
        settings['simulationSetup'] = simulationSetup[idx]
        settings['repetitions'] = repetitions/batchSize

        pointer = os.path.abspath(tempfile.mkstemp(suffix='.yml',text=True,dir='./tmp')[1])
        with open(pointer,'w') as f:
            f.write(yaml.dump(settings))
        # Open a pipe to the qsub command.
        output, input = popen2('qsub')
        
        # Customize your options here
        job_name = "jjtv_{0}_{1}".format(outputtype,idx)
        walltime = "10:00:00"
        processors = "nodes={1}:ppn={0}".format(min(queue_list[queue], repetitions/noOfBatches), nodes)
        analyzer = os.path.abspath('benchmark.py')
        command = ['python {0}'.format(analyzer),'-s', pointer, '-o', '${SCRDIR}/',
        '-t',outputtype
            #'XMLExamples/curated/BIOMD%010i.xml' % self.param,
        ]
        command = ' '.join(command)

        if outputtype == "atomize":
            tail_job_string = """%s
            cd ${SCRDIR}
            """ % (command)
        else:
            tail_job_string = """cd ${SCRDIR}
            %s
            """ % (command)

        job_string = """#!/bin/bash
        #PBS -N %s
        #PBS -l walltime=%s
        #PBS -l %s
        #$ -cwd
        #PBS -q %s

        echo Running on `hostname`
        echo workdir $PBS_O_WORKDIR

        ##PBS -M jjtapia@gmail.com
        ##PBS -m abe  # (a = abort, b = begin, e = end)
        PYTHONPATH=$PYTHONPATH:./
        PATH=/usr/local/anaconda/bin:$PATH
        SCRDIR=/scr/$PBS_JOBID

        #if the scratch drive doesn't exist (it shouldn't) make it.
        if [[ ! -e $SCRDIR ]]; then
                mkdir $SCRDIR
        fi

        cd $PBS_O_WORKDIR
        echo scratch drive ${SCRDIR}

        trap "cd ${SCRDIR};mv * $PBS_O_WORKDIR/%s" EXIT
        %s
        
        """ % (job_name, walltime, processors, queue, outputdirectory, tail_job_string)
        
        # Send job_string to qsub
        input.write(job_string)
        input.close()
        
        # Print your job and the system response to the screen as it's submitted
        #print(output.read())
        
        time.sleep(0.05)


def getSimulationSetup():
    # select folder where bngl files are located
    #bnglfiles = getValidFiles(os.path.join(home, 'workspace', 'bionetgen', 'bng2', 'Models2'), 'bngl')
    #bnglfiles = getValidFiles(os.path.join(home, 'workspace', 'bionetgen', 'parsers','SBMLparser','curated'), 'bngl')
    #bnglfiles = getValidFiles(os.path.join('.', 'bnglTest'), 'bngl')

    plaOptions = [['fEuler', 'midpt', 'rk4'], ['pre-neg:sb', 'Anderson:sb', 'pre-eps:sb'], ['0.01','0.03','0.05']]
    plaOptions = list(itertools.product(*plaOptions))
    simulationMethods = [['pla', 'pla_config=>' + '|'.join(x)] for x in plaOptions]
    simulationMethods.append(['ssa', ''])

    return simulationMethods
    '''    
    for idx, bngl in enumerate([bnglfiles[0]]):
        print('Processing {1}/{2}= {0}'.format(bngl, idx, len(bnglfiles)))
        try:
            bnglsimulate(bngl, simulationMethods, '1', 1)
        except pexpect.EOF:
            print 'error processing {0}'.format(bngl)
            continue

    print timings
    timings2 = deepcopy(timings)
    for fileName in timings:
        for method in timings[fileName]:
            timings2[fileName]['{0}_variance'.format(method)] = np.std(timings[fileName][method])
            timings2[fileName][method] = np.mean(timings[fileName][method])

    # file to store timings in. It will be stored as a dictionary of values. These can be sent to a pandas dataframe using
    # pandas.DataFrame.from_dict(<dict>)
    with open('results3.dump', 'wb') as f:
        pickle.dump(dict(timings2), f)
    '''


def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-i', '--input', type=str)
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('-q','--queue',type=str,help='queue to run in')
    parser.add_argument('-b','--batch',type=str,help='queue to run in')
    parser.add_argument('-r','--repetitions',type=str,help='queue to run in')
    return parser


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    simulationOptions = getSimulationSetup()
    fileName = getFiles(namespace.input, 'bngl')

    fileNameOptionsTemp = [fileName, simulationOptions]
    simulationSetup = list(itertools.product(*fileNameOptionsTemp))
    start_queue(simulationSetup, namespace.repetitions, namespace.output, namespace.queue, namespace.batch)
