#!/usr/bin/env python
import sys
from pp_util import load_jobfile, stampede_init, submit_cmdline
import argparse


parser = argparse.ArgumentParser(
    description='Run jobs with parallel python.')
parser.add_argument('job_script', type=str, help='Job script to be submitted.')
parser.add_argument(
    '-cluster_name', type=str, help='Name of the cluster',
    metavar='str', default='stampede')
args = parser.parse_args()
work_dir_list, cmdline_list = load_jobfile(args.job_script)
if args.cluster_name == 'stampede':
    jobserver, ncpus = stampede_init()
else:
    raise argparse.ArgumentError("Invalid cluster_name!")
active_nodes = jobserver.get_active_nodes()
active_cpus = sum(active_nodes.values())
print 'Active_nodes:', active_nodes
print 'N_cpus = %d, Active_cpus = %d' % (ncpus, active_cpus)
assert (ncpus == active_cpus)

print 'Starting sumbitting jobs...'
print '# of jobs = %d, # of cpus = %d' % (len(cmdline_list), ncpus)
if len(cmdline_list) > ncpus:
    sys.stderr.write('WARNING: More jobs than the total amount of CPUs\n')

jobs = []
for work_dir, cmdline in zip(work_dir_list, cmdline_list):
    jobs.append(
        jobserver.submit(
            submit_cmdline, (work_dir, cmdline),
            modules=('subprocess', 'os')))
jobserver.wait()

for i, job in enumerate(jobs):
    print '#####Job %4d#####' % i
    output, returncode = job()
    if returncode != 0:
        print(
            'ERROR: Job %4d returned non-zero exit status %d!!!'
            % (i, returncode))
    print output
print '####################'

jobserver.print_stats()
jobserver.destroy()
