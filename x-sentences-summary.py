import json
import networkx as nx
import string

def summary(sentences:set[str]) -> dict[str, int]:
    # PRE-PROCESSING
    G = nx.Graph()

    # 1. Construct all nodes, one node per sentence
    for sentence in sentences:
        G.add_node(sentence)



    # 2. Construct all edges, one edge per word
    # Edges are undirected, but will be converted
    # to directed by the PageRank library (later)
    for sentence in sentences:
        words = sentence.split()

        for rawWord in words:
            word = rawWord.translate((str.maketrans('', '', string.punctuation)))

            for node in G.nodes:
                if word in node:
                    G.add_edge(sentence, node)

    # 3. PageRank
    pr = nx.pagerank(G)
    print(pr)

    return []





# DEV: EVERYTHING PAST THIS POINT DEBUG AND TESTING
def main():
    with open('data/Abu Bakr.json') as file:
        loadedJSON = json.load(file)
        sentences = loadedJSON["sentences"]
        importantSentences = summary(set(sentences))
        print(importantSentences)

if __name__ == "__main__":
    main()