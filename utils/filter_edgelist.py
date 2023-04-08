from time import gmtime, strftime


def filter_out_outsiders(edgelist):
    """
    Take edgelist and filter out targets who aren't sources. The `edgelist` DataFrame must have columns `source` and `target`.
    """
    sources = set(edgelist["source"].unique())
    filtered = edgelist[edgelist["target"].apply(lambda x: x in sources)]
    print(f"Number of unique sources: {len(sources)}")
    print(f"Edgelist length before filtering: {len(edgelist)}")
    print(f"Edgelist length after filtering: {len(filtered)}")
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFiltered out outsider nodes")
    return filtered


def filter_out_original(edgelist, job_dir_og):
    """
    Take edgelist and filter out members of the original ID set. Use this function after filter_out_outsiders(). The `edgelist` DataFrame must have columns `source` and `target`.
    """
    # Load original
    with open(f"{job_dir_og}twitter_ids_og.csv") as f:
        ids_og = set(line.strip() for line in f.readlines())
    filter1 = edgelist["source"].apply(lambda x: x not in ids_og)
    print(filter1.head())
    filter2 = edgelist["target"].apply(lambda x: x not in ids_og)
    print(filter2.head())
    filtered = edgelist[(filter1) & (filter2)]
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFiltered out nodes from the original set"
    )
    return filtered
