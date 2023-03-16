import json
import networkx as nx
import string

def select(sentences:set[str], number:int):
    sentenceList = summary(sentences)
    result = []
    for i in range(0, len(sentenceList), (int) (len(sentenceList) / number)):
        result.append(sentenceList[i])
    return result

def summary(sentences:set[str]) -> list[str]:
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
    with open('data/ABBA.json') as file:
        loadedJSON = json.load(file)
        sentences = set(loadedJSON["sentences"])
        importantSentences = select(sentences, 6)

        for i in range(0, len(importantSentences)):
            sentence = importantSentences[i]
            print(f"SENTENCE {i + 1} IS THE SENTENCE \"{sentence}\"")

if __name__ == "__main__":
    main()