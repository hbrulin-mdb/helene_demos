# Create a params.py file with the following : 

```sh
conn_string = "MONGODB_CLUSTER_URI"
```

# launch monitor.py

# Failover without retryable writes

```sh
./continuous-insert.py 'mongodb+srv://<USER:PASS>@cluster0.bwqnw.mongodb.net/?retryWrites=false'
./continuous-read.py 'mongodb+srv://<USER:PASS>@cluster0.bwqnw.mongodb.net/?retryReads=false'
```

show error if there is one! (it is hard to get one!)

Back in the terminal/shell continuous output, keep visually scanning the output looking for when a failure is reported by the client application, from which you will be able to determine how long the client application is unable to write to the database, before being automatically failed over. 

Note: Atlas may take a few minutes before it schedules the primary failure action to be invoked on the database cluster.

Once the failure is shown in the output, terminate the running Python applications (Ctrl-C)

By calculating the difference in time between the last reported INSERT occurrence before the DB-CONNECTION-PROBLEM event and the first reported INSERT occurrence following the RECONNECTED-TO-DB you can see how long the application was unable to perform insert operations against the Atlas database during failover


# Failover with retryable writes

Restart the Python application again, this time providing an additional retry parameter, to instruct the application to employ MongoDB's retryable writes capability, e.g.:

```sh
./continuous-insert.py 'mongodb+srv://<USER:PASS>@cluster0.bwqnw.mongodb.net/?retryWrites=true'
./continuous-read.py 'mongodb+srv://<USER:PASS>@cluster0.bwqnw.mongodb.net/?retryReads=true'
```

Again, use the Atlas console's Test Failure feature, but this time notice that when Atlas reports that failover has been successfully completed, the Python application's output does not report any connection problems or service disruption.

# show metrics after with red, orange and brown lines




