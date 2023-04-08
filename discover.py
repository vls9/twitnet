from time import gmtime, strftime
import pandas as pd
import networkx as nx
from networkx.algorithms import community
from utils.filter_edgelist import filter_out_outsiders
from utils.job_load import (
    get_edgelist_job_dir_path,
    get_job_num,
    load_edgelist,
)


def get_in_degree_centrality(G, n=-1):
    """
    Compute in-degree centrality and return a Series of nodes' in-degree centrality. Use n for top N nodes, and n=-1 for all nodes.
    """
    d = dict(G.in_degree())
    data = {"id_str": [], "in_degree": []}
    for node, in_degree in d.items():
        data["id_str"].append(node)
        data["in_degree"].append(in_degree)
    if n == -1:
        df = pd.DataFrame(data).sort_values(by="in_degree", ascending=False)
    else:
        df = pd.DataFrame(data).sort_values(by="in_degree", ascending=False).head(n)
    return df


def initialize_graph(edgelist):
    """
    Initialize and return NetworkX graph object. edgelist must be a DataFrame with columns 'source' and 'target'
    """
    G = nx.from_pandas_edgelist(
        edgelist, source="source", target="target", create_using=nx.DiGraph
    )
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tInitialized graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
    )
    return G


def get_cutoff_perc():
    """
    Specify cutoff percentile `cutoff_perc` such that for a given community, only nodes followed by at least `cutoff_perc` fraction of the community.
    """
    try:
        return float(input("Specify cutoff percentile (e.g. 0.8, 0.66, 0.5): "))
    except:
        get_cutoff_perc()


def explore_graph(Gf, edgelist, cutoff_perc, min_community_size=3):
    """
    Explore graph and record results.
    """
    # Detect communities using the Girvan-Newman algorithm (based on betweenness centrality)
    communities_generator = community.girvan_newman(Gf)
    to_explore = set()
    failed = set()

    for comm in next(communities_generator):
        # From edgelist, filter out sources not in the community, keep outsiders
        comm_member_set = set(comm)
        comm_edgelist = edgelist[
            edgelist["source"].apply(lambda x: x in comm_member_set)
        ]
        print(f"Length of community edgelist: {len(comm_edgelist)}")
        G_comm = nx.from_pandas_edgelist(
            comm_edgelist, source="source", target="target", create_using=nx.DiGraph
        )
        in_deg_cent = get_in_degree_centrality(G_comm)
        in_deg_cutoff = cutoff_perc * len(comm_member_set)
        print(f"Community size: {len(comm_member_set)}")
        print(f"In-degree cutoff: {round(in_deg_cutoff, 2)}")
        in_deg_cent_cutoff = in_deg_cent[in_deg_cent["in_degree"] > (in_deg_cutoff)]
        print(
            f"Number of members before filtering out community members: {len(in_deg_cent_cutoff)}"
        )
        # Compute user IDs to explore--filter out community members
        in_deg_cent_cutoff_f = in_deg_cent_cutoff[
            in_deg_cent_cutoff["id_str"].apply(lambda x: x not in comm_member_set)
        ]
        if len(comm) < min_community_size:
            failed.update(in_deg_cent_cutoff_f["id_str"])
            print(
                f"Excluded {len(in_deg_cent_cutoff_f['id_str'])} users from exploration because of the community's small size ({len(comm)})"
            )
        else:
            to_explore.update(in_deg_cent_cutoff_f["id_str"])
            print(f"Added {len(in_deg_cent_cutoff_f)} users for exploration from community")
    fname = f"{job_dir}discover_{job_num}_{str(cutoff_perc).replace('.', '_')}.csv"
    with open(fname, "w") as f:
        f.writelines([i + "\n" for i in to_explore])

    failed_fname = (
        f"{job_dir}discover_failed_{job_num}_{str(cutoff_perc).replace('.', '_')}.csv"
    )
    with open(failed_fname, "w") as f:
        f.writelines([i + "\n" for i in failed])
    print(f"In total, added {len(to_explore)} users for exploration from all communities")
    print(
        f"Now run load.py, select option c (IDs from file) and paste this filename\n\n{fname}\n\nThen, select 0 (initial set only)"
    )
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExplored community graphs")
    return 0


job_num = get_job_num()
job_dir = get_edgelist_job_dir_path(job_num)

# Use unfiltered edgelist for exploration
edgelist = load_edgelist(job_dir)

# Use filtered edgelist (no outsiders) for community detection
filtered = filter_out_outsiders(edgelist)
Gf = initialize_graph(filtered)

# Explore graph
cutoff_perc = get_cutoff_perc()
explore_graph(Gf, edgelist, cutoff_perc, min_community_size=3)
