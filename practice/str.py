#!/usr/bin/python

str=raw_input("Enter the string")
if len(str)>2:
    first=str[0:2]
    second=str[-3:]
    print first,second
else:
    print "Emnpty"

c=len(str)
while c>=1:
    c=c-1
    print str[c]
