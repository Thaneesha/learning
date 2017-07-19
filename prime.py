#!/usr/bin/python

a=int(raw_input("enter the integre"))
if a == 2:
    print a,"is Prime"
if a>2:
    print 2,"is prime"
    for num in range(2,a):
        if ( num%2  == 0 ):
            flag=1
        else:
            print num,"is Prime"
else:
    print "Please enter integer above 2 "
