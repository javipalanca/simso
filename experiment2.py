#!/usr/bin/python3
# coding=utf-8

import sys
import os
from simso.core import Model
from simso.configuration import Configuration
import simso.generator.task_generator as task_generator
import csv
import numpy as np


class ResultExp(object):
    def __init__(self, name, i, result):
        self.name = name
        self.taskset_id = i
        self.task_migrations = sum(task.task_migration_count for task in
                                   result.tasks.values())
        self.migrations = 0
        self.preemptions = 0
        self.preemptions_inter = 0

        cycles_per_ms = result.model.cycles_per_ms

        for task in result.tasks.values():
            self.migrations += sum(job.migration_count for job in task.jobs)
            self.preemptions += sum(job.preemption_count for job in task.jobs)
            self.preemptions_inter += sum(job.preemption_inter_count
                                          for job in task.jobs)

        self.exceeded_count = sum(task.exceeded_count for task in
                                  result.tasks.values())

        self.response_time = 0
        for task in result.tasks.values():
            self.response_time += sum((job.response_time for job in task.jobs
                                       if job.response_time)) / len(task.jobs)
        self.response_time = (self.response_time / (len(result.tasks)
                              * cycles_per_ms))

        normalised_laxities = np.array(
            [(task.task.deadline - float(job.response_time) / cycles_per_ms)
             / task.task.period
             for task in result.tasks.values()
             for job in task.jobs
             if job.response_time and not job.aborted])
        self.avg_laxities = normalised_laxities.mean()
        self.std_laxities = normalised_laxities.std()
        self.job_count = len(normalised_laxities)

        self.on_schedule_count = result.scheduler.schedule_count

        self.timers = result.total_timers

    def save(self, c):
        c.writerow((self.taskset_id, self.name, self.preemptions_inter,
                    self.preemptions - self.preemptions_inter, self.migrations,
                    self.task_migrations, self.avg_laxities,
                    self.on_schedule_count, self.timers,
                    self.exceeded_count, self.job_count))

    @staticmethod
    def print_header(c):
        c.writerow(("taskset id", "scheduler", "preemptions", "sys preempt.",
                    "migrations", "task_migrations", "mean norm laxity",
                    "on schedule", "timers", "aborted jobs", "total jobs"))


def main(argv):
    schedulers = [
        "schedulers/RM.py", "schedulers/EDF.py", "schedulers/PriD.py",
        "schedulers/EDF_US.py", "schedulers/EDZL.py", "schedulers/LLF.py",
        "schedulers/MLLF.py",
        "schedulers/P_EDF.py", "schedulers/LB_P_EDF.py", "schedulers/EDHS.py",
        "schedulers/EKG.py", "schedulers/LRE_TL.py", "schedulers/DP_WRAP.py",
        "schedulers/BF.py", "schedulers/LLREF.py", "schedulers/PD2.py",
        "schedulers/ER_PD2.py", "schedulers/RUN.py"]

    schedulers = [
        "schedulers/EDF.py", "schedulers/EDZL.py", "schedulers/MLLF.py",
        "schedulers/P_EDF.py", "schedulers/EDHS.py", "schedulers/EKG.py",
        "schedulers/LRE_TL.py", "schedulers/LLREF.py", "schedulers/ER_PD2.py",
        "schedulers/RUN.py"]

    schedulers = ["schedulers/EDF.py", "schedulers/EDF2.py"]

    schedulers = ["schedulers/WC_U_EDF.py", "schedulers/U_EDF.py",
                  "schedulers/RUN.py", "schedulers/WC_RUN.py"]
    schedulers = ["schedulers/RUN.py", "schedulers/WC_RUN.py",
                  "/home/max/Documents/These/RTCSA/experiments/schedulers/WC_RUN.py"]
    schedulers = ["schedulers/WC_U_EDF.py", "schedulers/U_EDF.py",
                  "/home/max/Documents/These/RTCSA/experiments/schedulers/WC_U_EDF.py"]
    schedulers = ["schedulers/PD2.py", "schedulers/ER_PD2.py"]

    output = input("Output directory: ")
    os.mkdir(output)

    wcet_file = open(output + "/wcet.csv", "w")
    csv_wcet = csv.writer(wcet_file)
    ResultExp.print_header(csv_wcet)

    acet_file = open(output + "/acet.csv", "w")
    csv_acet = csv.writer(acet_file)
    ResultExp.print_header(csv_acet)

    if argv:
        for i, f in enumerate(argv):
            configuration = Configuration(f)
            for scheduler_name in schedulers:
                print(scheduler_name)
                configuration.scheduler_info.set_name(scheduler_name,
                                                      configuration.cur_dir)

                configuration.check_all()
                execute(configuration, "wcet", csv_wcet, wcet_file, i)
                execute(configuration, "acet", csv_acet, acet_file, i)
    else:
        # Manual configuration:
        configuration = Configuration()
        configuration.duration = 1000 * configuration.cycles_per_ms

        # Generate tasks:
        nsets = int(input("Number of experiments: "))
        n = int(input("Number of tasks: "))
        nb_proc = int(input("Number of processors: "))
        u = float(input("Load: "))

        u = task_generator.StaffordRandFixedSum(n, u, nsets)
        periods = task_generator.gen_periods_loguniform(n, nsets, 2, 100,
                                                        round_to_int=True)
        # Add processors:
        for i in range(1, nb_proc + 1):
            configuration.add_processor(name="CPU {}".format(i), identifier=i)

        for i, exp_set in enumerate(task_generator.gen_tasksets(u, periods)):
            for scheduler_name in schedulers:
                print(scheduler_name)
                configuration.scheduler_info.set_name(scheduler_name,
                                                      configuration.cur_dir)
                while configuration.task_info_list:
                    del configuration.task_info_list[0]
                id_ = 1
                for (c, p) in exp_set:
                    configuration.add_task(
                        name="T{}".format(id_), identifier=id_,
                        period=p, activation_date=0, wcet=c,
                        acet=c * .75, et_stddev=c * .1,
                        deadline=p, abort_on_miss=True)
                    id_ += 1

                # Check the configuration:
                configuration.check_all()

                # Save the current exp:
                configuration.save(output + "/exp_{}.xml".format(i))

                # Execute the simulation:
                execute(configuration, "wcet", csv_wcet, wcet_file, i)
                execute(configuration, "acet", csv_acet, acet_file, i)


def execute(configuration, etm, csv, csv_file, exp_id):
    scheduler_name = configuration.scheduler_info.name
    configuration.etm = etm
    model = Model(configuration)
    try:
        model.run_model()
        r = ResultExp(scheduler_name, exp_id, model.results)
        r.save(csv)
        csv_file.flush()
    except AssertionError as e:
        print(e)


if __name__ == "__main__":
    main(sys.argv[1:])
