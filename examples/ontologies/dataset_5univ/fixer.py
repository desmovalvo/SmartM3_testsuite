#!/usr/bin/python

import sys

# leggo il filename
filename = sys.argv[1]

# apri file
f = open(filename, "rw")

# crea un nuovo file
f_out = open("fixed_" + filename, "w")

# scorri file
for line in f:

    if "<rdf:RDF" in line:
    
        new_line = line + """
xml:base="http://swat.cse.lehigh.edu/onto/univ-bench.owl"
"""
        f_out.write(new_line)

    else:
        
        f_out.write(line)

# chiudi file
f.close()
f_out.close()
