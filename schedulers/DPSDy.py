"""
Deadline Prediction Scheduler algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler, Timer
from random import choice
from math import sqrt, ceil
from collections import defaultdict


class DPSDy(Scheduler):
    def init(self):
        self.ready_list = []
        self.windowsize = 100 #float(100.0)
        self.window_id = 0
        self.queue_index = 0
        self.default_quantum = 10
        self.timeline = defaultdict(list)
        self.started = False
      
    def reset_window(self, cpu):
        if self.started:
            self.window_id += 1
        else:
            self.started = True
        self.queue_index = 0
        #clean window
        self.timeline[self.window_id] = [job for job in self.timeline[self.window_id] if job.is_active()]

    def reschedule(self, cpu):
        cpu.resched()

    def on_activate(self, job):
        self.ready_list.append(job)
        prev = len(self.timeline[self.window_id])
        wcet = job.wcet
        w_id = self.window_id
        while wcet > 0:
            if sqrt(self.windowsize) > len(self.timeline[w_id]):
                self.timeline[w_id].append(job)
                wcet -= self.windowsize / 2**(self.timeline[w_id].index(job)+1)
            w_id += 1
        deadline = self.windowsize * w_id + self.windowsize
        job._absolute_deadline = job._task._task_info.deadline = deadline    
            
        if prev == 0 and len(self.timeline[self.window_id]) > 0:
            job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        self.preempt_timer.stop()

    def schedule(self, cpu):
        now = self.sim.now_ms()
        remaining_time_in_window = self.windowsize - (now % self.windowsize)
        if now % self.windowsize == 0:
            self.reset_window(cpu)

        if remaining_time_in_window > 0:
            try:
                current_job = self.timeline[self.window_id][self.queue_index]
                # if job has still reserved cpu time
                if current_job.is_running() and now < current_job.absolute_burst:
                    return (current_job, cpu)
            except:
                pass            
            # burst has finished and next prioritary job is selected
            try:
                job = self.timeline[self.window_id][self.queue_index]
                priority = self.queue_index + 1
                burst = self.windowsize / 2**priority
            except Exception as e:
                available = [job for job in self.timeline[self.window_id] if job.is_active()] + self.ready_list
                if len(available):
                    # Slack time, choose random job
                    job = choice(available)
                    burst = self.default_quantum
                else:
                    # Idle
                    return (None, cpu)

            if burst == 0: # gain time
                if self.ready_list:
                    job = choice(self.ready_list)
                burst = min(self.default_quantum, remaining_time_in_window)
            else: # adjust burst
                burst = min(remaining_time_in_window, (min(burst, job.ret)))

            if burst == 0 and remaining_time_in_window > 0:
                burst = remaining_time_in_window

            #print "[{3}] JOB {0}, scheduled with burst {1} until {2}".format(job.name, burst, now+burst, now)
            self.preempt_timer = Timer(self.sim, DPSDy.reschedule,
                              (self, self.processors[0]), ceil(burst),
                              one_shot=True, cpu=self.processors[0])
            job.absolute_burst = now + burst
            self.preempt_timer.start()                    

            self.queue_index += 1
            return (job, cpu)
