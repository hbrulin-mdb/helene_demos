# We start with full text search : Ghost in the shell
with keyword search, we get pretty good results. the first is very good, and we also get anime related results mixed in from our movies db. 

# if we switch to vector search, we still get ghost in the shell in the third result, but we're missing some of those anime related movies

so it works very well for text search, less for vector search.

we can improve that : 

# we do another query : scientists hunt ghost in new york

in vector search, we get ghostbusters in the top. very good hit

# we switch to text search
we don't get such good matches for the concept
so in this case vss is working well, not so well for vector search

# so if we go to recriprocal rank fusion

ghostbusters are not right at the top but near the top, and they were not there with full text search. so RFF gets us decent relevance for this query

# how does it handle ghost in the shell?
we again get a relevant result near the top, and we're still getting the anime related movies from the db in the result set as well. what this demonstrates is although the hybrid search approach doesn't make both queries the best, overall across these two queries, you get better relevance

# show query
so how does this work? 
you can see this works with a rankfusion stage, where we send our vector pipeline and then our full text pipeline as well. you can see our vector search uses our vector search stage with our query vector, and the full text search pipeline uses phrase matches... and we combine these two approaches in the rankfusion stage, and then applying some weighting to them as well. 
for another implementation, you might find that weighting vector results more relevant results, or that weighting text search is best

# using score fusion, we can also combine results, but this time using the scores. certain parameters can be adjusted : how the scores shoudl be noprmalized within each result set, for example, and how the ranking should be done. 

if we switch our score normalizing function from sigmoid to minmax, our ghost in the shell result pops to the top, and we can rank based on the avg score across lexical and vector searches for a given movie, or the sum, or simply take the maximum.

# show query
as with rank fusion, the query is a score fusion stage, with the two pipelines used as inputs. down here you can see thes eparameters being applied. 
you could also use other retrieval mechanisms as input pieplines, geospatial queries for example. 