import json
import networkx as nx
import string

def summary(sentences:set[str]) -> dict[str, float]:
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

    return sorted(pr, key=pr.get)





# DEV: EVERYTHING PAST THIS POINT DEBUG AND TESTING
def main():
    print("\n\n\nTESTING RESULTS")
    with open('data/14th Dalai Lama.json') as file:
        loadedJSON = json.load(file)
        sentences = loadedJSON["sentences"]
        importantSentences = summary(set(sentences))

        for i in range(0, len(importantSentences), 10):
            sentence = importantSentences[i]
            print(f"SENTENCE {i} IS THE SENTENCE \" {sentence} \"")

if __name__ == "__main__":
    main()