#!/usr/bin/python

import sys
import glob
import time
import getopt
import rdflib
import datetime
import traceback
from output_helpers import *
from smart_m3.m3_kp_api import *

sib_ip = "localhost"
sib_port = 7701
triple_list = []
total_triple = 0
elapsed_time = 0
owl_list = []
step = 100
clean = False

### READ COMMAND LINE PARAMETERS

cprint(True, "Pre-Test", "Reading command line arguments")
options, remainder = getopt.getopt(sys.argv[1:], 's:ct:o:', ['sib=', 'clean', 'step=', 'owlfolder='])
for opt, arg in options:

    if opt in ('-p', '--step'):
        step = arg

    elif opt in ('-o', '--owlfolder'):
        for owl_file in glob.glob(arg + "/*"):
            owl_list.append(owl_file)

    elif opt in ('-s', '--sib'):
        sib = arg    
        global sib_ip
        global sib_port
        sib_ip = sib.split(":")[0]
        sib_port = int(sib.split(":")[1])

    elif opt in ('-c', '--clean'):
        clean = True


### CONNECT TO THE SIB
cprint(True, "Pre-Test", "Connecting to %s:%s" % (sib_ip, sib_port))
try:
    kp = m3_kp_api(False, sib_ip, sib_port)
except Exception as e:
    print e.__str__()
    sys.exit()


### CLEAN
if clean:
    cprint(True, "Pre-Test", "Cleaning the sib")
    kp.load_rdf_remove([Triple(None, None, None)])

### PROCESSING THE FILE
for owl_file in owl_list:

    cprint(True, "Test", "Inserting owl file %s" % (owl_file))
    g = rdflib.Graph()
    g.parse(owl_file,  format='application/rdf+xml')
    
    for triple in g:
    
        # subject
        if unicode(type(triple[0])) == "<class 'rdflib.term.URIRef'>":
            sub = URI(unicode(triple[0]))
        else:
            sub = bNode(unicode(triple[0]))
    
        # predicate
        pred = URI(unicode(triple[1]))
    
        # object
        if unicode(type(triple[2])) == "<class 'rdflib.term.URIRef'>":
            ob = URI(unicode(triple[2]))
        elif unicode(type(triple[2])) == "<class 'rdflib.term.Literal'>":
            ob = Literal(triple[2].encode('utf-8'))
        else:
            ob = bNode(unicode(triple[2]))
    
        # build the triple list
        a = Triple(sub, pred, ob)
        triple_list.append(a)
        if len(triple_list) == 100:
            try:
                start_time = int(round(time.time() * 1000))
                cprint(True, "Test", "[%s] Inserting %s triples (%s) [%s/%s]" % (total_triple, step, owl_file, owl_list.index(owl_file)+1, len(owl_list)))
                kp.load_rdf_insert(triple_list)
                end_time = int(round(time.time() * 1000))
                elapsed_time = elapsed_time + (end_time - start_time)
            except:
                print "ERRORE:"
                print triple
                print traceback.print_exc()
                sys.exit(0)
            total_triple = total_triple + len(triple_list)
            triple_list = []
            
    if len(triple_list) > 0:
        total_triple = total_triple + len(triple_list)
        start_time = int(round(time.time() * 1000))
        cprint(True, "Test", "[%s] Inserting %s triples (%s) [%s/%s]" % (total_triple, len(triple_list), owl_file, owl_list.index(owl_file)+1, len(owl_list)))
        kp.load_rdf_insert(triple_list)
        end_time = int(round(time.time() * 1000))
        elapsed_time = elapsed_time + (end_time - start_time)
    

# END OF GAMES

kp.load_query_sparql("""SELECT (COUNT(?x) as ?num)
WHERE {?x ?y ?z}""")
    
print "Triple inserted: %s" % (total_triple)
print "Triple into the SIB: %s" % (kp.result_sparql_query[0][0][2])
print "Elapsed time: %s ms " % (elapsed_time)
