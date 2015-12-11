#!/usr/bin/python
###############################################################################
### imports
###############################################################################
import sys
import os
import subprocess
import time
import datetime

###############################################################################
### utility functions
###############################################################################
def usage():
    print "usage:", __file__, " --user <USER>"

def format_time(t):
    t = datetime.datetime.fromtimestamp(t)
    return '[{time}]'.format(time=t.strftime('%Y-%m-%d %H:%M:%S'))

def log(*m, **kw):
    m = list(m)
    if 'time' in kw:
        m.insert(0, format_time(kw['time']))
    sys.stdout.write(' '.join(m))
    sys.stdout.write('\n')
    sys.stdout.flush()
    return

def check_output(*args, **kwargs):
    for k, v in kwargs.iteritems():
        args.append(' '.join(k, v))
    o, e = subprocess.Popen(
        ' '.join(args), shell=True, executable='/bin/bash',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()
    if e and len(e):
        raise Exception(e)
    return o


###############################################################################
### helper classes
###############################################################################
class Queue(object):
    
    def __init__(self, status_cmd = None, submit_file = None):
        self._user = None
        self._status_cmd = status_cmd 
        self._submit_file = submit_file
        if not os.path.exists(submit_file):
            raise Exception(submit_file+" does not exist!!!")
        self._sleep_time = 5 #*60

    def is_empty(self):
        # run status_cmd and check output
        o = check_output(self._status_cmd)
        return bool(len(o.split('\n')))      

    def submit_jobs(self):
        # source submit_file
        o = check_output('source', self._submit_file)
        return True
    
    def perpetuate(self):
        while True:
            try:
                if not self.is_empty():
                    time.sleep(self._sleep_time)
                    continue
                log('Queue is empty', time=time.time())
                self.submit_jobs()
                log(self._submit_file,
                    'has been submitted',
                    time=time.time())
            except Exception as e:
                log(e.__str__())
                time.sleep(self._sleep_time)
        return False


class SLURMQueue(Queue):

    def __init__(self, user = ''):
        Queue.__init__(
            self,
            status_cmd = 'squeue --user {user} | tail --lines=+2'.format(user=user),
            submit_file = './sbatchMINI'
        )
        self._user = user


class PBSQueue(Queue):

    def __init__(self, user = ''):
        Queue.__init__(
            self,
            status_cmd = 'qstat | tail --lines=+3'.format(user=user),
            submit_file = './qsubMINI'
        )
        self._user = user
        

###############################################################################
### helper functions
###############################################################################
def get_queue(**kwargs):
    hostname = os.uname()[1]
    if 'sherlock' in hostname:
        return SLURMQueue(user=kwargs['user'])
    elif 'biox3' in hostname:
        return PBSQueue(user=kwargs['user'])
    else:
        raise Exception("Hostname not vaild!")


def get_queue_auto(**kwargs):
    if os.path.exists('/usr/bin/sbatch'):
        return SLURMQueue(user=kwargs['user'])
    elif os.path.exists('/usr/bin/qsub'):
        return PBSQueue(user=kwargs['user'])
    else:
        raise Exception("Could not fine sbatch or qsub!!!")


###############################################################################
### main function
###############################################################################
def auto_queue(*args, **kwargs):

    ### TODO: should this just be a method of Queue?
    #q = get_queue(**kwargs)
    q = get_queue_auto(**kwargs)
    q.perpetuate()


###############################################################################
### main script
###############################################################################
if __name__ == '__main__':
    
    args = sys.args[1:]
    kwargs = {}
    
    if '--user' in args:
        idx = args.index('--user')
        args.pop(idx)
        kwargs['user'] = args.pop(idx)
    else:
        usage()

    sys.exit(auto_queue(*args, **kwargs))
