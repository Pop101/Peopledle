import json
from modules.Graph import WeightedUndirectedGraph as Graph
from modules.Graph import pagerank
import string

def select(sentences:set[str], number:int):
    sentenceList = summary(sentences)
    result = []
    for i in range(0, len(sentenceList), (int) (len(sentenceList) / number)):
        result.append(sentenceList[i])
    return result

def summary(sentences:set[str]) -> list[str]:
    # PRE-PROCESSING
    G = Graph()

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

            for node in G:
                if word in node:
                    G.add_edge(sentence, node)

    # 3. PageRank
    ranks = pagerank(G.adjacency_matrix(), 100, 0.85)
    ranks = sorted(zip(G, ranks), reverse=True, key=lambda x: x[1])
    ranks = [rank[0] for rank in ranks]

    return ranks





# DEV: EVERYTHING PAST THIS POINT DEBUG AND TESTING
def main():
    print("\n\n\nTESTING RESULTS")
    with open('data/Abraham Lincoln.json') as file:
        loadedJSON = json.load(file)
        sentences = set(loadedJSON["sentences"])
        importantSentences = select(sentences, 6)

        for i, sentence in enumerate(importantSentences):
            print(f"SENTENCE {i + 1} IS THE SENTENCE \"{sentence}\"")

if __name__ == "__main__":
    main()