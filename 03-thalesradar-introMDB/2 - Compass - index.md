# Show current list of indexes

# Single index

- faire une query 
{
  "type": "aircraft"
}

Show the explain

Ajouter index et remontrer

Show the projection.


# Compound Index

Create index : 

{
  "type": 1,
  "metadata.last_update": -1,
  "velocity.speed": 1
}

- perfect ESR match

{
  "type": "aircraft",
  "velocity.speed": { "$gt": 200 }
}

Sort : 
{
  "metadata.last_update": -1
}

- - sidenote : show the prefix thing by just filtering on type:aircraft

- bad index order : create another index
{
  "type": 1,
  "velocity.speed": 1,
  "metadata.last_update": -1
}

Run again : 
{
  "type": "aircraft",
  "velocity.speed": { "$gt": 200 }
}

Sort : 
{
  "metadata.last_update": -1
}

Show explain : MongoDB can’t use the index as efficiently to satisfy the sort once a range is encountered too early in the index.

You’ll often see either:

an extra SORT stage (in-memory sort), or

a higher number of keys/docs examined.

# faire un laius, aussi possible d'indexer dans les tableaux, partial indexes etc... mais un point important à vous montrer car la data sur le radar est temporaire, les index TTL


# TTL index

TTL indexes are single-field indexes on a Date field (or array of dates).

MongoDB removes expired docs via a background TTL monitor, so deletion is not immediate.

Expect removals typically within ~60 seconds after expiry (can be a bit more/less depending on load/config).

Go to create index : 
- { "metadata.last_update": 1 }
- options : create TTL : 30 secondes

On peut aussi avec un champ expireAt, et mettre le délai à 0 secondes.