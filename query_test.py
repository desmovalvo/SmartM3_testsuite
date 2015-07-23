#!/usr/bin/python

# requirements
import csv
import sys
import glob
import pygal
import getopt
import timeit
import datetime
from termcolor import *
from smart_m3.m3_kp_api import *
from pygal.style import LightColorizedStyle

# initial variables
cleaner = """DELETE { ?s ?p ?o }
WHERE { ?s ?p ?o }"""
kp_list = []
sib_list = {}
owl_list = []
query_results = {}
loadonly = False

# print helper
def cprint(status, phase, message):
    if status:
        print colored(phase + "> ", "blue", attrs=["bold"]) + message
    else:
        print colored(phase + "> ", "red", attrs=["bold"]) + message

# help string
help_string = """
query_test - parameters:

--owl=folder -> loads every owl file contained in the folder
--queryfile=file -> loads every query contained in the file* (omit the .py extension)
--query=queryname -> the name of the query to be tested
--sibs=SIBip1:SIBport1:SIBdesc1%...%SIBipN:SIBportN:SIBdescN -> to specify the SIBs to test
--iterations=N -> how many time the test must be repeated
--clean -> tells the program to clean the SIBs before starting the test
--loadonly -> exits after loading the ontologies
--help -> shows this message

* the query file must contain a dictionary named query where each value
contains the SPARQL query and the key is the name of the query
"""

# read command line parameters
# paramters are:
# - the folder containing the initial KB to load
# - query to be performed
# - SIBs to be queried (this is a list of sib specified as SIB_ADDRESS1:SIB_PORT1:NAME%SIB_ADDRESS2:SIB_PORT2:NAME2%...)
# - number of iterations

options, remainder = getopt.getopt(sys.argv[1:], 'o:f:q:s:i:clh', ['owl=', 'queryfile=', 'query=', 'sibs=', 'iterations=', 'clean', 'loadonly', 'help'])
for opt, arg in options:

    if opt in ('-o', '--owl'):
        for owl_file in glob.glob(arg + "/*"):
            owl_list.append(owl_file)

    elif opt in ('-f', '--queryfile'):
        querymodule = __import__(arg)

    elif opt in ('-q', '--query'):
        query_name = arg
        query_text = querymodule.query[query_name]

    elif opt in ('-s', '--sibs'):
        sibs = arg    
        for sib in sibs.split("%"):

            # get sib data
            s_ip = sib.split(":")[0]
            s_port = int(sib.split(":")[1])
            s_name = sib.split(":")[2]
            sib_list[s_name] = s_ip + ":" + str(s_port)

    elif opt in ('-i', '--iterations'):
        iterations = int(arg)

    elif opt in ('-c', '--clean'):
        clean = True

    elif opt in ('-l', '--loadonly'):
        loadonly = True

    elif opt in ('-h', '--help'):
        print help_string
        sys.exit()

cprint(True, "Init", "Read command line parameters")

# generate the name for the output files
d = datetime.datetime.now().strftime("%Y%m%d%H%M")
csv_file = d + "-query" + str(query_name) + "-iter" + str(iterations) + ".csv"
svg_file = d + "-query" + str(query_name) + "-iter" + str(iterations) + ".svg"

# connections to the SIBs:
cprint(True, "Init", "Connecting to the SIBs...")
for k in sib_list.keys():

    try:
        kp = m3_kp_api(False, sib_list[k].split(":")[0], int(sib_list[k].split(":")[1]), k)
        kp_list.append(kp)
        cprint(True, "Init", "Connected to sib %s" % (k))
    except:
        cprint(False, "Init", "Connection to sib %s failed!" % (k))
        sys.exit()

# initialize the csv file
csv_file_stream = open(csv_file, "w")
csv_file_writer = csv.writer(csv_file_stream, delimiter=',', quoting=csv.QUOTE_MINIMAL)

# initialize and configure the svg file
bar_chart = pygal.Bar(style=LightColorizedStyle, x_title="", y_title="Time (ms)")
bar_chart.title = """Time to perform query %s""" % (query_name)

# iterate
for kp in kp_list:
    
    # clean the SIB
    if clean:
        cprint(True, "Pre-Test", "Cleaning SIB %s" % (kp.__dict__["theSmartSpace"][0]))
        kp.load_query_sparql(cleaner)

    # load the KB
    for owl_file in owl_list:
        cprint(True, "Pre-Test", "Loading owl file %s on SIB %s [%s/%s]" % (owl_file, kp.__dict__["theSmartSpace"][0], owl_list.index(owl_file)+1, len(owl_list)))
        kp.load_rdfxml_insert_from_file(owl_file)
    if loadonly:
        continue

    # perform the query
    query_results[kp_list.index(kp)] = []
    for i in range(iterations):
        cprint(True, "Test", "Performing query %s on %s (iteration %s)" % (query_name, kp.__dict__["theSmartSpace"][0], i))
        query_time = timeit.timeit(lambda: kp.load_query_sparql(query_text), number = 1)
        query_results[kp_list.index(kp)].append(query_time)

    # compute the average
    sum = 0
    for el in query_results[kp_list.index(kp)]:
        sum += el
    avg = sum / len(query_results[kp_list.index(kp)])

    # write the CSV file and plot the graph
    row = []
    row.append(kp.__dict__["theSmartSpace"][0])
    for qr in query_results[kp_list.index(kp)]:
        row.append(round(qr,3))
    row.append(round(avg,3))
    csv_file_writer.writerow(row)
    bar_chart.add(kp.__dict__["theSmartSpace"][0], avg)

# render the svg graph
bar_chart.render_to_file(svg_file)

# Close csv file
csv_file_stream.close()
