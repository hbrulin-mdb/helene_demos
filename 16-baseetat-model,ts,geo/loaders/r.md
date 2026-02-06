# jdb: 15M copies of document_jdb_events.json
python3 load_jdb_events.py \
  --uri "mongodb+srv://helenebrulin:pwd@cluster1.bwqnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1" \
  --db baseetat \
  --file document_jdb_events.json \
  --batch-size 1000 --unordered



python3 load_history.py \
  --uri "mongodb+srv://helenebrulin:pwd@cluster1.bwqnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1" \
  --db baseetat \
  --file document_history.json \
  --batch-size 1000 --unordered