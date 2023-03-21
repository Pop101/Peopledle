import json
from modules.Graph import WeightedUndirectedGraph as Graph
from modules.Graph import pagerank
from modules.stopwords import stopwords
import re



def select(ranked_sentences:dict[str, float], number:int) -> list[str]:
    # Selects the N most differently-ranked sentences
    
    ranked_sentences = sorted(ranked_sentences.items(), key=lambda x: x[1], reverse=True)
    return [ranked_sentences[i][0] for i in range(0, len(ranked_sentences), len(ranked_sentences) // number)][::-1]

def summary(sentences:set[str]) -> dict[str, float]:
    # PRE-PROCESSING
    G = Graph()

    # 1. Construct all nodes, one node per sentence
    for sentence in sentences:
        G.add_node(sentence)



    # 2. Construct all edges, one edge per word
    # Edges are undirected, but will be converted
    # to directed by the PageRank library (later)
    for sentence in sentences:
        for word in re.split(r"\s+|-", sentence):
            word = re.sub(r"[^\w█']", '', word).lower()

            if not word or word in stopwords or '█' in word:
                continue

            for node in G:
                if word in node:
                    G.add_edge(sentence, node)

    # 3. PageRank
    ranks = pagerank(G.adjacency_matrix(), 20, 0.65)
    ranks = dict(zip(G, ranks))
    
    return ranks





# DEV: EVERYTHING PAST THIS POINT DEBUG AND TESTING
def main():
    print("\n\n\nTESTING RESULTS")
    with open('data/Abraham Lincoln.json') as file:
        loaded_json = json.load(file)
        sentences = set(loaded_json["sentences"])
        
    ranked_sentences = summary(sentences)
    important_sentences = select(ranked_sentences, 5)

    for i, sentence in enumerate(important_sentences):
        print(f"SENTENCE {i + 1} IS THE SENTENCE \"{sentence}\"")

if __name__ == "__main__":
    main()