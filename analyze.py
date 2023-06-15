import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from time import sleep, strftime, gmtime
from utils.filter_edgelist import filter_out_original, filter_out_outsiders
from utils.job_load import get_edgelist_job_dir_path, get_job_num, load_edgelist
from utils.twitter_auth import get_twitter_api


def initialize_graph(edgelist):
    """
    Initialize NetworkX graph object.
    """
    G = nx.from_pandas_edgelist(
        edgelist, source="source", target="target", create_using=nx.DiGraph
    )
    print(f"Nodes: {G.number_of_nodes()}\nEdges: {G.number_of_edges()}")
    return G


def get_in_degree_centrality_with_nodelist(G, job_dir, fields=[], nodelist_name="", n=-1):
    """
    Compute in-degree centrality and return a Series of top n nodes. Use n=-1 for all nodes.
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
    nodelist_dict = (
        pd.read_csv(
            f"{job_dir}nodelists/nodelist{nodelist_name}.csv",
            index_col=0,
            dtype={"id_str": str},
        )
        .set_index("id_str")
        .to_dict(orient="index")
    )
    if not fields:
        fields = ["screen_name", "followers_count", "friends_count"]
    for field in fields:
        df[field] = df["id_str"].apply(lambda x: nodelist_dict[x][field])
    return df


def get_id_list(edgelist):
    """
    Get list of Twitter IDs from edgelist.
    """
    s1 = set(edgelist["source"].unique())
    s2 = set(edgelist["target"].unique())
    return s1.union(s2)


def make_nodelist(api, job_dir, ids, fields=[]):
    """
    Load nodelist--Twitter data about specified IDs. 
    API reference(s): https://docs.tweepy.org/en/stable/api.html#tweepy.API.get_user and https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/user
    """
    # Load default value of fields
    if not fields or len(fields) == 0:
        fields = [
            "id_str",
            "name",
            "screen_name",
            "followers_count",
            "friends_count",
            "verified",
        ]
    nodelist = []
    nodelist_failed = set()
    for id in ids:
        try:
            user = api.get_user(user_id=id)._json
            # Construct nodelist, list of dicts. Dict key names correspond to field names from user object. Grab fields specified in var fields
            nodelist.append({field: user[field] for field in fields})
            sleep(0.1)
        except Exception as e:
            print(repr(e))
            nodelist_failed.add(id)
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExtracted nodelist")
    # Save nodelist to CSV
    os.mkdir(f"{job_dir}nodelists/")
    sleep(1)
    pd.DataFrame(nodelist).to_csv(f"{job_dir}nodelists/nodelist.csv")
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tSaved nodelist to CSV")
    return 0


def set_attributes_from_nodelist(G, job_dir, nodelist_name=""):
    """
    Set node attributes for nodes in G.
    """
    # Load nodelist from file
    nodelist = pd.read_csv(
        f"{job_dir}nodelists/nodelist{nodelist_name}.csv",
        index_col=0,
        dtype={"id_str": str},
    )
    # Modify nodelist DataFrame into attrs dict
    attrs = nodelist.set_index("id_str").to_dict("index")
    nx.set_node_attributes(G, attrs)
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tSet node attributes for graph for nodelist in job {job_num}"
    )
    return G


def visualize_graph(G, job_dir):
    """
    Visualize graph and save it to file.
    """
    # Draw figure
    node_sizes = [i * 20 for i in dict(G.in_degree).values()]
    f = plt.figure(figsize=(10, 10))
    pos = nx.spring_layout(G, k=5)
    nx.draw(
        G,
        pos=pos,
        labels=nx.get_node_attributes(G, "screen_name"),
        node_size=node_sizes,
        with_labels=True,
    )
    # Save figure
    fname = f"{job_dir}viz/{strftime('%Y_%m_%d__%H_%M_%S', gmtime())}.svg"
    if not os.path.exists(f"{job_dir}viz/"):
        os.mkdir(f"{job_dir}viz/")
    plt.savefig(fname, dpi=300)
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tGraph visualized and file saved for job {job_num}"
    )
    return 0


def generate_new_nodelist(edgelist, job_dir):
    """
    Prepare to make new nodelist and execute it.
    """
    ids = get_id_list(edgelist)
    api = get_twitter_api()
    make_nodelist(api, job_dir, ids, fields=[])
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tGenerated new nodelist for job {job_num}"
    )
    return 0


def analyze_network_structure(G):
    """
    Analyze the structure of network G.
    """
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    n_edges_max = n_edges * (n_edges - 1)
    density = nx.density(G)
    print(f"Number of nodes: {n_nodes}")
    print(f"Number of edges: {n_edges}")
    print(f"Maximum possible number of edges: {n_edges_max}")
    print(f"Density: {density}")

    transitivity = nx.transitivity(G)
    print(f"Transitivity: {transitivity}")

    is_sc = nx.is_strongly_connected(G)
    print(f"Strongly connected: {is_sc}")
    if nx.is_strongly_connected(G) == False:
        # Get largest SC component
        sc_components = nx.strongly_connected_components(G)
        largest_sc_component = max(sc_components, key=len)
        lscc_subgraph = G.subgraph(largest_sc_component)
        n_outside_nodes = n_nodes - len(lscc_subgraph.nodes())
        print(
            f"Number of nodes outside the largest strongly connected component: {n_outside_nodes}"
        )

        diameter = nx.diameter(lscc_subgraph)
        print(f"Diameter (of the largest strongly connected component): {diameter}")
    else:
        diameter = nx.diameter(G)
        print(f"Diameter (of the only strongly connected component): {diameter}")
    return 0


def get_largest_component(G):
    """
    Find and return the largest strongly connected component of G.
    """
    return G.subgraph(max(nx.strongly_connected_components(G), key=len))


# Load edgelist
job_num = get_job_num()
job_dir = get_edgelist_job_dir_path(job_num)
edgelist = load_edgelist(job_dir)

filters = input(
    "Select group(s) of nodes to filter out\n\ta : outsiders\n\tb : original set\nType 'a' and/or 'b' or click Enter:\n"
)
if filters:
    if "a" in filters:
        edgelist = filter_out_outsiders(edgelist)
    if "b" in filters:
        edgelist = filter_out_original(edgelist, job_dir_og=job_dir)

# Load edgelist
job_dir = get_edgelist_job_dir_path(job_num)
# If nodelist doesn't exist
if not os.path.exists(f"{job_dir}nodelists/nodelist.csv"):
    # Generate new nodelist
    generate_new_nodelist(edgelist, job_dir)
else:
    is_new_nodelist = input(
        "Generate new nodelist? For 'n', existing nodelist will be used. Type 'y' or 'n':\n"
    )
    if is_new_nodelist == "y":
        generate_new_nodelist(edgelist, job_dir)

G = initialize_graph(edgelist)
G = set_attributes_from_nodelist(G, job_dir)
analyze_network_structure(G)
get_in_degree_centrality_with_nodelist(G, job_dir).to_csv(f"files/in_deg_{job_num}.csv")
visualize_graph(G, job_dir)
