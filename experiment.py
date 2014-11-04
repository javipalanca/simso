#!/usr/bin/python
# coding=utf-8

import sys
from simso.core import Model
from simso.configuration import Configuration
import simso.generator.task_generator as task_generator


def main(argv):
    schedulers = [
        "schedulers/RM.py", "schedulers/EDF.py", "schedulers/PriD.py",
        "schedulers/EDZL.py", "schedulers/RUN.py", "schedulers/EKG.py",
        "schedulers/P_EDF.py", "schedulers/LRE_TL.py", "schedulers/DP_WRAP.py",
        "schedulers/LLREF.py", "schedulers/LLF.py", "schedulers/PD2.py",
        "schedulers/BF.py", "schedulers/EDHS.py"]

    # Configuration manuelle :
    configuration = Configuration()
    configuration.duration = 1000 * configuration.cycles_per_ms

    # Generate tasks:
    n = 10
    nsets = 10
    u = 3.99

    u = task_generator.StaffordRandFixedSum(n, u, nsets)
    periods = task_generator.gen_periods_uniform(n, nsets, 10, 100,
                                                 round_to_int=True)
    # Ajout d'un processeur.
    configuration.add_processor(name="CPU 1", identifier=1)
    configuration.add_processor(name="CPU 2", identifier=2)
    configuration.add_processor(name="CPU 3", identifier=3)
    configuration.add_processor(name="CPU 4", identifier=4)

    for i, exp_set in enumerate(task_generator.gen_tasksets(u, periods)):
        print("==================================")
        for scheduler_name in schedulers:
            configuration.scheduler_info.set_name(scheduler_name,
                                                  configuration.cur_dir)
            print("{}:".format(scheduler_name))
            while configuration.task_info_list:
                del configuration.task_info_list[0]
            id_ = 1
            for (c, p) in exp_set:
                configuration.add_task(name="T{}".format(id_), identifier=id_,
                                       period=p, activation_date=0, wcet=c,
                                       deadline=p, abort_on_miss=True)
                id_ += 1

            # Vérification de la config.
            configuration.check_all()

            # Initialisation de la simu à partir de la config.
            model = Model(configuration)
            # Exécution de la simu.
            try:
                model.run_model()
                print("Aborted jobs:", sum(
                    model.results.tasks[task].exceeded_count
                    for task in model.task_list))
                assert sum(model.results.tasks[task].exceeded_count
                           for task in model.task_list) == 0, "aborted jobs"
            except AssertionError as e:
                print(e)
                configuration.save("exp_{}.xml".format(i))


if __name__ == "__main__":
    main(sys.argv[1:])
