#!/usr/bin/env python3
##
# Script to continuously read the latest document from the MongoDB database/
# collection 'AUTO_HA.records'
# This should be run together with continuous-insert.py
#
# Prerequisite: Install latest PyMongo driver and other libraries, e.g:
#   $ sudo pip3 install pymongo dnspython
#
# For usage details, run with no params (first ensure script is executable):
#   $ ./continuous-read.py
##
import sys
import random
import time
import datetime
import pymongo


####
# Main start function
####
def main():
    print('')

    if len(sys.argv) < 2:
        print('Error: Insufficient command line parameters provided')
        print_usage()
    else:
        uri = sys.argv[1].strip()
        retry = False

        if (len(sys.argv) >= 3):
            retry = True if (sys.argv[2].strip().lower() == 'retry') else False

        peform_reads(uri, retry)


####
# Perform the continuous database read workload, sleeping for 10 milliseconds
# between each read operation
####
def peform_reads(uri, retry):
    mongodb_url = uri
    print(f'Connecting to:\n {mongodb_url}\n')
    connection = pymongo.MongoClient(mongodb_url, retryWrites=retry, retryReads=retry)
    db = connection[DB_NAME]
    connect_problem = False
    count = 0

    while True:
        try:            
            count += 1

            # Latest document is the one with the highest val
            highest = db.records.find().sort('val', pymongo.DESCENDING).limit(1)[0]["val"]

            if (count % 30 == 0):
                print(f'{datetime.datetime.now()} - Count={count}  Highest={highest}')            

            if (connect_problem):
                print(f'{datetime.datetime.now()} - RECONNECTED-TO-DB')
                connect_problem = False
            else:
                time.sleep(0.01)
        except KeyboardInterrupt:
            print
            sys.exit(0)
        except Exception as e:
            print(f'{datetime.datetime.now()} - DB-CONNECTION-PROBLEM: '
                  f'{str(e)}')
            connect_problem = True


####
# Print out how to use this script
####
def print_usage():
    print('\nUsage:')
    print('$ ./continuous-insert.py <mongodb_uri> <retry>')
    print('\nExample: (run script WITHOUT retryable reads enabled)')
    print('$ ./continuous-insert.py mongodb+srv://<username>:<password>@<hostname>/<authDB>')
    print('$or')
    print('$ ./continuous-insert.py mongodb://<username>:<password>@<hostname1>:<port1>,<hostname2>:<port2>,<hostname3>:<port3>/<authDB>?replicaSet=<rsName>')
    print('\nExample: (run script WITH retryable reads enabled):')
    print('$ ./continuous-insert.py mongodb+srv://<username>:<password>@<hostname>/<authDB>?retryReads=true retry')
    print('$or')
    print('$ ./continuous-insert.py mongodb://<username>:<password>@<hostname1>:<port1>,<hostname2>:<port2>,<hostname3>:<port3>/<authDB>?replicaSet=<rsName>&retryReads=true retry')
    print()


# Constants
DB_NAME = 'AUTO_HA'
TTL_INDEX_NAME = 'date_created_ttl_index'


####
# Main
####
if __name__ == '__main__':
    main()