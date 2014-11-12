"""
Benefits-based Deadline Prediction Scheduler algorithm for uniprocessor architectures.
"""
import math
from simso.core import Scheduler, Timer, JobEvent, ProcEvent
from random import choice
from collections import defaultdict


class BDPS(Scheduler):
    def init(self):
        self.ready_list = []
        self.windowsize = 100
        self.window_id = 0
        self.queue_index = 0
        self.default_quantum = 10
        self.timeline = defaultdict(list)
        self.window_usage = defaultdict(lambda: self.windowsize)
        self.started = False
        
        try:
            self.MAX_PRIORITY = self.data["max_priority"]
        except KeyError:
            self.MAX_PRIORITY = 20
        try:
            self.MAX_B = self.data["max_b"]
        except KeyError:
            self.MAX_B = 1000.0
      
    def reset_window(self, cpu):
        if self.started:
            self.window_id += 1
        else:
            self.started = True
        self.queue_index = 0
        #clean window
        self.timeline[self.window_id] = [job for job in self.timeline[self.window_id] if job[0].is_active()]

    def reschedule(self, cpu):
        cpu.resched()

    def on_activate(self, job):
        try:
            job.a = job.data['a']
            job.b = job.data['b']
        except KeyError:
            job.a = 0.0
            job.b = self.MAX_B
        if job.a == 1.0:
            job.a = 0.0
        try:
            job.priority = job.data["priority"]
        except KeyError:
            job.priority = 1.0
        
        self.ready_list.append(job)
        prev = len(self.timeline[self.window_id])
        wcet = job.wcet
        w_id = self.window_id
        while wcet > 0:
            if self.window_usage[w_id] > 0:
                f = ((job.b/float(self.MAX_B)) * ((self.MAX_PRIORITY-job.priority)/self.MAX_PRIORITY) * (1-job.a))
                slot = float("{0:.2f}".format(max(f * self.windowsize, 1.0)))
                slot = min(self.window_usage[w_id], slot)
                self.timeline[w_id].append((job, slot))
                self.window_usage[w_id] -= slot
                wcet -= slot
            w_id += 1
        deadline = self.windowsize * w_id + self.windowsize
        job._absolute_deadline = job._task._task_info.deadline = deadline    
            
        if prev == 0 and len(self.timeline[self.window_id]) > 0:
            job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        self.preempt_timer.stop()
        seconds = (self.sim.now_ms() - job.activation_date) / 1000.0
        benefit = job.b * math.e ** (-job.a * seconds)
        job.add_custom_event(JobEvent(self, JobEvent.TEXTLABEL, data="{0:.2f}".format(benefit)))

    def schedule(self, cpu):
        now = self.sim.now_ms()
        remaining_time_in_window = float("{0:.2f}".format(self.windowsize - (now % self.windowsize)))
        if now % self.windowsize == 0:
            self.reset_window(cpu)
            cpu.monitor.observe(ProcEvent(ProcEvent.SEPARATOR))

        if remaining_time_in_window > 0:
            try:
                current_job = self.timeline[self.window_id][self.queue_index][0]
                # if job has still reserved cpu time
                if current_job.is_running() and now < current_job.absolute_burst:
                    return (current_job, cpu)
            except:
                pass            
            # burst has finished and next prioritary job is selected
            try:
                job, burst = self.timeline[self.window_id][self.queue_index]
            except Exception as e:
                available = [job[0] for job in self.timeline[self.window_id] if job[0].is_active()] + self.ready_list
                if len(available):
                    # Slack time, choose random job
                    job = choice(available)
                    burst = self.default_quantum
                else:
                    # Idle
                    return (None, cpu)

            burst = float("{0:.2f}".format(burst))
            if burst == 0: # gain time
                if self.ready_list:
                    job = choice(self.ready_list)
                burst = self.default_quantum
            # adjust burst
            ret = float("{0:.2f}".format(job.ret))
            burst = min(remaining_time_in_window, burst, ret)

            if burst == 0 and remaining_time_in_window > 0:
                burst = remaining_time_in_window

            self.preempt_timer = Timer(self.sim, BDPS.reschedule,
                              (self, self.processors[0]), burst,
                              one_shot=True, cpu=self.processors[0])
            job.absolute_burst = now + burst
            self.preempt_timer.start()                    

            self.queue_index += 1
            return (job, cpu)
