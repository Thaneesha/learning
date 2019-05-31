#!/usr/bin/python

fh=open("text","w")
list=["My name is Sabitha\n","My hubby is Sathesh\n","My son is Devkanth\n","My daughter is Thaneesha\n"]
list1=["My name is Sabitha","My hubby is Sathesh","My son is Devkanth","My daughter is Thaneesha"]
fh.writelines(list)
fh.writelines(list1)
fh.close()
fh=open("text")
print fh.read()
fh.close()
