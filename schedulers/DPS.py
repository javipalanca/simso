"""
Deadline Prediction Scheduler algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler, Timer
from random import choice
from math import sqrt, ceil


class DPS(Scheduler):
    def init(self):
        self.ready_list = []
        self.windowsize = 100
        self.window_id = 0
        self.queue_index = 0
        self.default_quantum = 10
        self.window_queue = []

    def fill_window_queue(self):
        while sqrt(self.windowsize) > len(self.window_queue) and len(self.ready_list) > 0:
            self.window_queue.append(self.ready_list.pop(0))
        
    def reset_window(self, cpu):
        self.window_id += 1
        self.queue_index = 0

        #remove finished jobs
        self.window_queue = [job for job in self.window_queue if job.is_active()]
        
        # fill the window queue
        self.fill_window_queue()        
        
    def reschedule(self, cpu):
        cpu.resched()

    def on_activate(self, job):
        self.ready_list.append(job)
        priority = len(self.window_queue) + self.ready_list.index(job) + 1
        # deadline prediction
        job._absolute_deadline = job._task._task_info.deadline = ceil(job._activation_date + (2**priority) * job.wcet)
        prev = len(self.window_queue)
        self.fill_window_queue()
        if prev == 0 and len(self.window_queue) > 0:
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
                current_job = self.window_queue[self.queue_index]
                # if job has still reserved cpu time
                if current_job.is_running() and now < current_job.absolute_burst:
                    return (current_job, cpu)
            except:
                pass            
            # burst has finished and next prioritary job is selected
            try:
                job = self.window_queue[self.queue_index]
                priority = self.queue_index + 1
                burst = self.windowsize / 2**priority
            except Exception as e:
                available = [job for job in self.window_queue if job.is_active()] + self.ready_list
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
            self.preempt_timer = Timer(self.sim, DPS.reschedule,
                              (self, self.processors[0]), ceil(burst),
                              one_shot=True, cpu=self.processors[0])
            job.absolute_burst = now + burst
            self.preempt_timer.start()                    

            self.queue_index += 1
            return (job, cpu)
