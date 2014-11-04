#!/usr/bin/python
# coding=utf-8

from distances import circular_stack
from seq_generator import generate_sequence

N = int(raw_input("Longueur de la séquence : "))
F = int(raw_input("Footprint : "))
filename = raw_input("Chemin du fichier de sortie : ")

seq = generate_sequence(N, F)
h = circular_stack(seq)

f = open(filename, 'w')

for i, v in enumerate(h):
    f.write(str(i) + ' ' + str(float(v) / N) + '\n')

f.close()
