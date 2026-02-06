# Show the search index creation and explain dynamic vs static indexing
# explain analyzers
# check the index in compass
# in compass aggregation

[
  {
    $search: {
      index: "default",
      text: {
        query: "device",
        path: "name"
      }
    }
  },
  {
    $project: {
      name: 1,
      manufacturer: 1,
      score: { $meta: "searchScore" }
    }
  },
  { $sort: { score: -1 } },
  { $limit: 20 }
]

What this shows : 
- stemming
- tokenization
- relevance scoring
- partial matches
- uppercase/lowercase

# fuzzy search
[
  {
    $search: {
      index: "default",
      text: {
        query: "acmme",
        path: "manufacturer",
        fuzzy: { maxEdits: 1 }
      }
    }
  },
  { $limit: 10 }
]

# autcomplete - would require regex without Atlas search - cannot show without changing the index

# can mix with filters

[
  {
    $search: {
      index: "default",
      text: {
        query: "device",
        path: ["name"]
      }
    }
  },
  {
    $match: {
      manufacturer: "acme",
      initialized: true
    }
  },
  { $limit: 10 }
]