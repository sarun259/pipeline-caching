Goal: In research, you might have a pipeline with various steps consuming and generating large amounts of data, and you might experiment with different strategies. The point of this project is to build a cache system for such a pipeline, where a cache is invalidated if and only if its dependencies have changed.

Design:

User should make a .conf file describing the computation DAG. 
Each line of the .conf file is of the form “<node name> [<innode 1 name>,..., <innode k name>] <invocation> <deps>” where 
Node names are arbitrary strings not containing spaces
Invocation is a quotation-surrounded string containing {INPUT1}, …, {INPUTk} and {OUTPUT} such that if you replace inputs and output with filenames then you can run invocation on the command line to produce output based on the contents of inputs
<deps> is a comma-separated list of filenames, which should essentially be the files that the invocation depends on (e.g. the location of the source code of the invocation binary)

User runs “run_pipeline <conf filename> <target node> <max memory> (optional: - - redo)
This does the following:
Iterate through nodes necessary to get to target node in topological order. If not a DAG, throw error.
We have a folder cache/, and within it a folder for each node. In that folder, we put caches of that node’s file. These caches are named by a hash of 1) the innode files and 2) the deps of all edges leading to the node, at the time the invocation was made. 
We store a data structure which stores the names of the currently existing caches for each node and when they were last used.. (We populate this data structure once at the beginning).
At each node, we check if we need to run the invocation by seeing if any of the caches under that node have the same hash as the hash of the current dependencies. If so, we update the “time of last usage” of that cache to now, otherwise we make the invocation and create a new cache. If redo is specified, we always make the invocation.
If our caches ever exceeds the max memory specified by the user, we evict caches using an LRU policy.

You should keep the core logic in one file. Everything peripheral should be in its own helper file, e.g. topological sort, hashing, LRU logic, parsing. The core logic should be incredibly clean and concise.

You should also create an example conf showing that your implementation works as intended.
