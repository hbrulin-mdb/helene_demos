# Notes

# Launch
```sh
docker compose -f docker-compose-spark.yml up
```

http://localhost:8888/tree : jupyter

http://localhost:9001/login : admin, password -> le bucket est déjà créé. 

Upload the timetravel notebook in jupyter. Start running it. 

# Jupyter step 8

Je crée la définition de ma table. -> le metadata file. - see example file 1 in this folder. 

# Jupyter step 9
Inserts data -> maintenant dans mon folder metadata, j'ai plus de fichiers. J'ai tjrs le fichier de définition, mais j'ai une autre définition avec des metadonnées en plus. ce fichier pointe vers un manifest list, qui est le fichier avro.   Cete description là est faite dans un snapshot, qui a comme séquence 1. Snapshot 0 avec séquence1, qui pointe vers un manifestfile qui est le fichier avro. -> see example file 2. 

Le manifest list pointe vers un fichier avro -> fichier qui commence par snap. c'est le snapshot 0. 
Le snapshot, pointe vers un manifest list, qui est l'autre fichier avro. il pointe sur les deux fichiers parquet qui sont dans data. 

Dans mon warehouse - data, j'ai mes deux fichiers parquet avec ma data. 
C'est académique d'avoir un fichier parquet par row, on peut faire autrement. 

# Jupyter step 11
Edits row 1 -> now I have new files in metadata, and in data as well. 


# Jupyter step 16
rollback sur un snapshot précédent. 

# Jupyter step 17
evert to timestamp

# Jupyter step 18
reset current snapshot to snapshot that we restored. 

# Jupyter step 19
Then check the state of data. 


# Stop

delete volumes when turning down docker compose : 

```sh
docker compose -f docker-compose-spark.yml down -v
```


# Other

- iceberg rest est utilisé pour que spark puisse interagir avec le server. 
- mc utilisé pour lancer lignes de commandes automatisées.