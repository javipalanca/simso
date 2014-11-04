"""
Round Robin Scheduler algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler, Timer
from Queue import Queue

class RR(Scheduler):
    def init(self):
        self.ready_list = Queue()
        self.running_job = None
        self.quantum = 1 # ms
        self.timer = Timer(self.sim, RR.reschedule,
                          (self, self.processors[0]), self.quantum, one_shot=False,
                          cpu=self.processors[0])
        self.timer.start()
        
    def reschedule(self, cpu):
        if not self.ready_list.empty():
            cpu.resched()

    def on_activate(self, job):
        self.ready_list.put(job)
        job.cpu.resched()

    def on_terminated(self, job):
        self.running_job = None
        job.cpu.resched()

    def schedule(self, cpu):
        if not self.ready_list.empty():
            job = self.ready_list.get()
            if self.running_job is not None:
                self.ready_list.put(self.running_job)
            self.running_job = job
        else:
            job = self.running_job
        return (job, cpu)
