#!/usr/bin/env python3
##
# Script to continuously inserts new documents into the MongoDB database/
# collection 'AUTO_HA.records'
#
# Prerequisite: Install latest PyMongo driver and other libraries, e.g:
#   $ sudo pip3 install pymongo dnspython
#
# For usage details, run with no params (first ensure script is executable):
#   $ ./continuous-insert.py
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

        peform_inserts(uri, retry)


####
# Perform the continuous database insert workload, sleeping for 10 milliseconds
# between each insert operation
####
def peform_inserts(uri, retry):
    mongodb_url = uri
    print(f'Connecting to:\n {mongodb_url}\n')
    connection = pymongo.MongoClient(mongodb_url, retryWrites=retry, retryReads=retry)
    db = connection[DB_NAME]
    db.records.drop()
    db.records.create_index([('val', pymongo.DESCENDING)])
    db.records.create_index('date_created', name=TTL_INDEX_NAME, expireAfterSeconds=7200)
    print('Ensured there is a TTL index to prune records after 2 hours\n')
    print('Inserting records continuously...')
    connect_problem = False
    count = 0

    while True:
        try:            
            count += 1

            db.records.insert_one({
                'val': count,
                'date_created': datetime.datetime.now()
            })

            if (count % 30 == 0):
                print(f'{datetime.datetime.now()} - INSERTED TILL {count}')            

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
    print('\nExample: (run script WITHOUT retryable writes enabled)')
    print('$ ./continuous-insert.py mongodb+srv://<username>:<password>@<hostname>/<authDB>')
    print('$or')
    print('$ ./continuous-insert.py mongodb://<username>:<password>@<hostname1>:<port1>,<hostname2>:<port2>,<hostname3>:<port3>/<authDB>?replicaSet=<rsName>')
    print('\nExample: (run script WITH retryable writes enabled):')
    print('$ ./continuous-insert.py mongodb+srv://<username>:<password>@<hostname>/<authDB>?retryWrites=true retry')
    print('$or')
    print('$ ./continuous-insert.py mongodb://<username>:<password>@<hostname1>:<port1>,<hostname2>:<port2>,<hostname3>:<port3>/<authDB>?replicaSet=<rsName>&retryWrites=true retry')
    print()


# Constants
DB_NAME = 'AUTO_HA'
TTL_INDEX_NAME = 'date_created_ttl_index'


####
# Main
####
if __name__ == '__main__':
    main()