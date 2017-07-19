#!/usr/bin/python

str="Hi my name Hi is sabitha hi"
list=str.split()
wc=len(list)
tc=0
print "Word count",wc
for  entry in list:
    if entry == "Hi" or entry == "hi":
        tc+=1
print "Character count",tc
