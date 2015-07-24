#!/usr/bin/python

# requirements
import sys
import time
import getopt
import rdflib
import traceback
from termcolor import *
from smart_m3.m3_kp_api import *

# initialization
sib_ip = "localhost"
sib_port = 10111
n3file = "sp2b.n3"

# read command line parameters
try: 
    opts, args = getopt.getopt(sys.argv[1:], "s:n:", ["sib=", "n3file="])
    for opt, arg in opts:
        if opt in ("-s", "--sib"):
            sib_ip = arg.split(":")[0]
            sib_port = int(arg.split(":")[1])
        elif opt in ("-n", "--n3file"):
            n3file = arg

except getopt.GetoptError:
    print colored("init> ", "red", attrs=["bold"]) + "Usage: python insert.py --sib=sib_ip:port --n3file=n3file"
    sys.exit()


# connect to the SIBs
conn_ok = False
while not conn_ok:
    try:
        print colored("init> ", "blue", attrs=['bold']) + "Connecting to the SIB"
        kp = m3_kp_api(False, sib_ip, sib_port, "X")
        conn_ok = True
    except Exception as e:
        print colored("init> ", "red", attrs=['bold']) + e.__str__()
        print colored("init> ", "red", attrs=['bold']) + "Retrying connection in a while..."


# extract triples from the n3 file
print colored("init> ", "blue", attrs=['bold']) + "Extracting triples from n3 file...",
g = rdflib.Graph()
res = g.parse(n3file, format='n3')
print "Done!"

# clean the SIB
kp.load_rdf_remove([Triple(None, None, None)])

# insert the triples on the SIB
print colored("init> ", "blue", attrs=['bold']) + "Starting the insertion"
counter = 0
triple_list = []
print colored("init> ", "blue", attrs=["bold"]) + "Insertion",
for triple in res:

    s = []
    for t in triple:

        if type(t).__name__  == "URIRef":
            s.append( URI(t.toPython()) )
            
        elif type(t).__name__  == "Literal":
            s.append( Literal(t.toPython()) )

        elif type(t).__name__  == "BNode":
            s.append( bNode(t.toPython()) )

    ins_ok = False
    if len(s) == 3:
        counter += 1
        triple_list.append(Triple(s[0], s[1], s[2]))
        if counter % 100 == 0:            
            while ins_ok != True:
                try:
                    kp.load_rdf_insert(triple_list)                    
                    ins_ok = True
                    triple_list = []
                    print counter
                except:
                    print traceback.print_exc()
                    print colored("init> ", "red", attrs=['bold']) + e.__str__()
                    print colored("init> ", "red", attrs=['bold']) + "Retrying insert in a while..."
                    time.sleep(3)            

while ins_ok != True:
    try:
        kp.load_rdf_insert(triple_list)                    
        ins_ok = True
        triple_list = []
        print counter
    except:
        print traceback.print_exc()
        print colored("init> ", "red", attrs=['bold']) + e.__str__()
        print colored("init> ", "red", attrs=['bold']) + "Retrying insert in a while..."
        time.sleep(3)            

print "Done!"

# check about the number of triples
kp.load_query_rdf(Triple(None, None, None))
r = kp.result_rdf_query
print colored("init> ", "blue", attrs=["bold"]) + "The SIB contains %s triples" % (str(len(r)))
if len(r) < counter:
    print colored("init> ", "blue", attrs=["bold"]) + "The SIB contains less than %s triples" % (counter)
    sys.exit()
    
