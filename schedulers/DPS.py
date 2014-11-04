"""
Deadline Prediction Scheduler algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler, Timer
from random import choice
from math import sqrt


class DPS(Scheduler):
    def init(self):
        self.ready_list = []
        self.windowsize = 100
        self.window_id = 0
        self.queue_index = 0
        self.default_quantum = 10
        self.window_queue = []
        
        self.window_timer = Timer(self.sim, DPS.reset_window,
                          (self, self.processors[0]), self.windowsize,
                          one_shot=False, cpu=self.processors[0])
                          
        #self.window_timer.start()
        
        self.processors[0].resched()
        
    def reset_window(self, cpu):
        self.window_id += 1
        self.queue_index = 0
        
        # fill the window queue
        while sqrt(self.windowsize) > len(self.window_queue) and len(self.ready_list) > 0:
            self.window_queue.append(self.ready_list.pop(0))
            
        print "RESET WINDOW", self.sim.now_ms()
        
        #cpu.resched()
        
    def reschedule(self, cpu):
        cpu.resched()

    def on_activate(self, job):
        self.ready_list.append(job)
        priority = self.ready_list.index(job) + 1
        # deadline prediction
        job._absolute_deadline = job._activation_date + (2**priority) * job.wcet
        if len(self.ready_list) == 1:
            job.cpu.resched()

    def on_terminated(self, job):
        if self.queue_index >= self.window_queue.index(job) and self.queue_index!=0:
            #self.queue_index-=1
            self.window_queue.remove(job)
        if job in self.ready_list:
            self.ready_list.remove(job)
        #self.ready_list_index -= 1
        job.cpu.resched()

    def schedule(self, cpu):
        now = self.sim.now_ms()
        remaining_time_in_window = self.windowsize - (now % self.windowsize)
        if now % self.windowsize == 0:
            self.reset_window(cpu)
        if True: #remaining_time_in_window > 0:
            try:
                current_job = self.window_queue[self.queue_index]
                # if job has still reserved cpu time
                if current_job.is_running() and now < current_job.absolute_burst:
                    print "GOT CURRENT JOB"
                    return (current_job, cpu)
            except:
                pass            
            # burst has finished and next priority job is selected
            try:
                job = self.window_queue[self.queue_index]
                priority = self.queue_index + 1
                burst = self.windowsize / 2**priority
                print "GOT NEW JOB", priority, burst
            except Exception as e:
                print "EXCEPTION", e
                if self.ready_list:
                    job = choice(self.ready_list)
                    burst = self.default_quantum
                    print "GOT RANDOM JOB", burst
                else:
                    job = None
                    print "GONE IDLE"
                    return (None, cpu)

            burst = max(0, min(remaining_time_in_window, burst))
            if burst == 0 and remaining_time_in_window > 0:
                burst = remaining_time_in_window

            print "JOB {0}, scheduled with burst {1} until {2}".format(job.name, burst, now+burst)
            self.preempt_timer = Timer(self.sim, DPS.reschedule,
                              (self, self.processors[0]), burst,
                              one_shot=True, cpu=self.processors[0])
            job.absolute_burst = now + burst
            self.preempt_timer.start()                    

            self.queue_index += 1
            return (job, cpu)


    def old_schedule(self, cpu):
        now = self.sim.now_ms()
        remaining_time_in_window = self.windowsize - (now % self.windowsize)
        print "REMAINING TIME", remaining_time_in_window
        if self.ready_list and remaining_time_in_window > 0:
            try:
                current_job = self.ready_list[self.ready_list_index]
                # if job has still reserved cpu time
                if current_job.is_running() and now < current_job.absolute_burst:
                    print "GOT CURRENT JOB"
                    return (current_job, cpu)
            except:
                pass
            # burst has finished and next priority job is selected
            try:
                job = self.ready_list[self.ready_list_index]
                priority = self.ready_list_index + 1
                burst = self.windowsize / 2**priority
                print "GOT NEW JOB", priority, burst
            except:
                job = choice(self.ready_list)
                burst = self.default_quantum
                print "GOT RANDOM JOB", burst
            
            burst = max(0, min(remaining_time_in_window, burst))
            if burst == 0 and remaining_time_in_window > 0:
                burst = remaining_time_in_window

            print "JOB {0}, scheduled with burst {1} until {2}".format(job.name, burst, now+burst)
            self.preempt_timer = Timer(self.sim, DPS.reschedule,
                              (self, self.processors[0]), burst,
                              one_shot=True, cpu=self.processors[0])
            job.absolute_burst = now + burst
            self.preempt_timer.start()                    

            self.ready_list_index += 1
            return (job, cpu)
