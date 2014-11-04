"""
Implementation of the PriD scheduler as introduced by Goossens et al. in
Priority-Driven Scheduling of Periodic Task Systems on Multiprocessors.
"""
from simso.core import Scheduler
from math import ceil


class PriD(Scheduler):
    """EDF(k) scheduler"""
    def init(self):
        self.ready_list = []
        self.kfirst = []

        tasks = sorted(self.task_list, key=lambda x: -x.wcet / x.period)
        kmin = 1
        mmin = None
        u = sum(x.wcet / x.period for x in tasks)
        for k, task in enumerate(tasks):
            u -= task.wcet / task.period
            m = k + ceil(u / (1 - task.wcet / task.period))
            if mmin is None or mmin > m:
                kmin = k + 1
                mmin = m

        self.kfirst = tasks[:kmin]

    def on_activate(self, job):
        if job.task in self.kfirst:
            job.priority = 0
        else:
            job.priority = job.absolute_deadline
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        else:
            job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # Key explanations:
            # First the free processors
            # Among the others, get the one with the greatest deadline
            # If equal, take the one used to schedule
            key = lambda x: (
                1 if not x.running else 0,
                x.running.priority if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            job = min([j for j in self.ready_list if j.is_active()],
                      key=lambda x: x.priority)

            if (cpu_min.running is None or
                    cpu_min.running.priority > job.priority):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                return (job, cpu_min)
