import numpy as np
from collections import OrderedDict

# BIG ISSUE: self[k] is the only way to convert from graph index to node
# However it is supposed to be user accessible and thus deletion works different
# would be fixed by a good bijection between graph index and node


class Node:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return f"<Node: {self.data}>"

    def __repr__(self):
        return f"<Node: {self.data}>"

    def __eq__(self, other):
        if not isinstance(other, Node):  # could use getattr(other, "data", None) instead
            return False
        return self.data == other.data

    def __hash__(self):
        if isinstance(self.data, dict):
            return hash(tuple(self.data.items()))
        try:
            return hash(self.data)
        except TypeError:
            return hash(tuple(self.data.__dict__.items()))


class WeightedDirectedGraph:
    def __init__(self, iterable=None):
        self.adjacency = OrderedDict()  # adj list, maps node -> list[(node, weight)]

        for node in iterable or []:
            self.add_node(node)

    def add_node(self, node):
        if node in self:
            raise ValueError("Duplicate Node")

        if not isinstance(node, Node):
            node = Node(node)

        self.adjacency[node] = list()

    def remove_node(self, node):
        if node not in self:
            return

        if not isinstance(node, Node):
            node = Node(node)

        # Delete all edges to this node
        for k, v in self.adjacency.items():
            v = list(filter(lambda edge: edge[0] != node, v))
            self.adjacency[k] = v

        # Delete all edges from this node
        del self.adjacency[node]

    def add_edge(self, src, dst, weight=1.0):
        if type(weight) not in (int, float):
            raise ValueError("Weight must be number")
        if not (src in self and dst in self):
            raise ValueError("Source or destination node not in graph")

        if not isinstance(src, Node):
            src = Node(src)
        if not isinstance(dst, Node):
            dst = Node(dst)

        # Duplicate edges btw 2 nodes allowed
        self.adjacency[src].append((dst, weight))

    def remove_edges_between(self, src, dst):
        if src not in self or dst not in self:
            return

        if not isinstance(src, Node):
            src = Node(src)
        if not isinstance(dst, Node):
            dst = Node(dst)

        self.adjacency[src] = list(filter(lambda x: x[0] != dst, self.adjacency[src]))

    def remove_edges_of(self, node):
        # leaves a node without edges
        if node not in self:
            return

        if not isinstance(node, Node):
            node = Node(node)

        self.adjacency[node] = list()

    def get_neighbors(self, node):
        if node not in self:
            raise ValueError("Node not in graph")

        if not isinstance(node, Node):
            node = Node(node)

        return sorted(((edge[0].data, edge[1]) for edge in self.adjacency[node]), key=lambda x: x[1])

    def adjacency_list(self):
        # shallow copy (may be a problem)
        return self.adjacency.copy()

    def adjacency_matrix(self) -> np.ndarray:
        mtrx = np.zeros((len(self), len(self)))

        to_index = {node: i for i, node in enumerate(self.adjacency)}
        for i, (_, edges) in enumerate(self.adjacency.items()):
            for dst, weight in edges:
                mtrx[i, to_index[dst]] += weight

        return mtrx

    def __len__(self):
        return len(self.adjacency)

    def __iter__(self):
        return iter(x.data for x in self.adjacency)

    def __str__(self):
        return f"<Graph with {len(self.adjacency)} nodes>"

    def __repr__(self):
        adj_list = dict()
        for k, v in self.adjacency.items():
            adj_list.update({k.data: [(edge[0].data, edge[1]) for edge in v]})

        return f"<Graph: {adj_list}>"

    def __getitem__(self, node_index):
        return list(self.adjacency.keys())[node_index].data

    def __contains__(self, node):
        if not isinstance(node, Node):
            node = Node(node)
        return node in self.adjacency

    def __delitem__(self, node):
        self.remove_node(node)

    def __setitem__(self, node_idex, new_node):
        if node_idex not in self:
            raise ValueError("Node not in graph")

        if not isinstance(new_node, Node):
            new_node = Node(new_node)

        # Super super untested

        # Copy old node's edges to new node
        self.adjacency[new_node] = self.adjacency[Node(self[node_idex])]

        # Move new node to the old node's index
        node_list = list(self.adjacency.keys())
        node_list[node_idex] = new_node
        self.adjacency = OrderedDict(zip(node_list, self.adjacency.values()))

        # Move all edges to old node to new node
        for k, v in self.adjacency.items():
            for i, edge in enumerate(v):
                if edge[0] == Node(self[node_idex]):
                    v[i] = (new_node, edge[1])


class WeightedUndirectedGraph(WeightedDirectedGraph):
    def __init__(self, iterable=None):
        super().__init__(iterable)

    def add_edge(self, src, dst, weight=1.0):
        super().add_edge(src, dst, weight)
        super().add_edge(dst, src, weight)

    def remove_edges_between(self, src, dst):
        super().remove_edges_between(src, dst)
        super().remove_edges_between(dst, src)

    def remove_edges_of(self, node):
        super().remove_edges_of(node)

        # Must also remove all edges to this node
        for k, v in self.adjacency.items():
            v = list(filter(lambda edge: edge[0] != node, v))
            self.adjacency[k] = v


def pagerank(M, num_iterations: int = 100, d: float = 0.85):
    """PageRank algorithm with explicit number of iterations. Returns ranking of nodes (pages) in the adjacency matrix.
    Parameters
    ----------
    M : numpy array
        adjacency matrix where M_i,j represents the link from 'j' to 'i'
    num_iterations : int, optional
        number of iterations, by default 100
    d : float, optional
        damping factor, by default 0.85

    Returns
    -------
    numpy array
        a vector of ranks such that v_i is the i-th rank from [0, 1],
        v sums to 1

    """

    # Preprocess to ensure all columns sum to 1
    M_column_sum = np.sum(M, axis=0)
    M = M / M_column_sum

    N = M.shape[1]
    v = np.ones(N) / N
    M_hat = d * M + (1 - d) / N

    for _ in range(num_iterations):
        v = M_hat @ v
    return v


if __name__ == "__main__":
    graph = WeightedUndirectedGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    graph.add_edge("A", "B", 1.0)
    graph.add_edge("B", "C", 1.0)

    print(repr(graph))
    print("First node:", graph[0])
    print("Neighbors of A:", graph.get_neighbors("A"))
    print("Adj Matrix:\n", graph.adjacency_matrix())

    print("Removing node B:")
    graph.remove_node("B")
    # print(repr(graph))
    print("First node:", graph[0])
    print("2ND node:", graph[1])
    print("Neighbors of A:", graph.get_neighbors("A"))
    print("Adj Matrix:\n", graph.adjacency_matrix())

    print("Running Simple PageRank:")
    graph = WeightedUndirectedGraph()
    graph.add_node("popular.com")
    graph.add_node("amog.us")
    graph.add_node("fingernails.win")
    graph.add_node("wiki.org")
    graph.add_edge("popular.com", "amog.us", 1)
    graph.add_edge("popular.com", "fingernails.win", 3)
    graph.add_edge("popular.com", "wiki.org", 7)
    graph.add_edge("amog.us", "fingernails.win", 1)
    graph.add_edge("amog.us", "fingernails.win", 1)

    print(graph)
    print("Adj Matrix:\n", graph.adjacency_matrix())
    ranks = pagerank(graph.adjacency_matrix(), 100, 0.85)
    ranks = sorted(zip(graph, ranks), reverse=True, key=lambda x: x[1])
    print("Ranks:")
    for site, rank in ranks:
        print(f"\t{site}: {rank}")
