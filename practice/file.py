#!/usr/bin/python
filename="text"
c=0
fh=open(filename,"r")
for line in fh.readlines():
    print "line",line
    list=line.split()
    for word in list:
        if word == "My":
            c+=1
print "Coun",c
