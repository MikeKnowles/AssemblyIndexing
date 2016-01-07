#!/usr/bin/env python
__author__ = 'mikeknowles'

from glob import glob
from os import system
from os.path import getsize, split
from multiprocessing import Pool


def Printer(file):
    print "Processing", file


def worker(jobs):
    file, dir = jobs
    Printer(file)
    try:
        if getsize(file) != getsize(dir + "/" + split(file)[1]):
            system("cp %s %s" % (file, dir))
    except OSError:
        system("cp %s %s" % (file, dir))


def multiwor(jobs):
    p = Pool(12)
    p.map(worker, jobs)


def finish(jobs):
    for job in jobs:
        job.join()
    return jobs

jobs = []
for file in glob("/nas/akoziol/WGS_Spades/20*/BestAssemblies/*.fasta"):
    jobs.append((file, "/nas/akoziol/WGS_Spades/AssemblyData/Assemblies/"))
for file in glob("/nas/akoziol/WGS_Spades/*/reports/*.json"):
    jobs.append((file, "/nas/akoziol/WGS_Spades/AssemblyData/JsonReports/"))
for file in glob("/nas/akoziol/WGS_Spades/*/reports/*_CombinedMetadataReport.tsv"):
    jobs.append((file, "/nas/akoziol/WGS_Spades/AssemblyData/SummaryReports/"))
multiwor(jobs)
