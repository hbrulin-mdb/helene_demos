# Run embeddevices.py to add text field and vector field to each device
# look at the updated documents in devices collection

# Create Vector Search Index

{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    },
    { "type": "filter", "path": "manufacturer" },
    { "type": "filter", "path": "generation" },
    { "type": "filter", "path": "technology" }
  ]
}

# generate a query vector with the script

python3 embedquery.py "outdoor e-ink metro station screen low power"

# copy the output and paste into the semanticsearch.json file -> run the query in compass
# same with semanticsearch with filter