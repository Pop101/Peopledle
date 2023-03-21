import json
from Graph import WeightedUndirectedGraph as Graph
from Graph import pagerank
from stopwords import stopwords
from determinism import random, randint, reseed, set_seed
import re



def select(ranked_sentences:dict[str, float], number:int) -> list[str]:
    # Selects the N most differently-ranked sentences
    
    ranked_sentences = sorted(ranked_sentences.items(), key=lambda x: x[1], reverse=True)
    return [ranked_sentences[i][0] for i in range(0, len(ranked_sentences), len(ranked_sentences) // number + 1)][::-1]

def randomize_const(ranked_sentences:dict[str, float], const:float, seed = 0) -> dict[str, float]:
    # Randomizes the ranking of each sentence by a constant
    # This is to prevent the same sentences being selected
    # every time
    # Note that the const is scaled by the average ranking
    average_rank = sum(ranked_sentences.values()) / len(ranked_sentences)
    const = average_rank * const
    
    set_seed(seed)
    for sentence in ranked_sentences:
        ranked_sentences[sentence] += (random() - 0.5) * 2 * const
        reseed()
    
    return ranked_sentences

def randomize_scalar(ranked_sentences:dict[str, float], scalar:float, seed = 0) -> dict[str, float]:
    # Randomizes the ranking of each sentence by a scalar
    # This is to prevent the same sentences being selected
    # every time
    # Note that the scalar is not scaled by the average ranking
    set_seed(seed)
    for sentence in ranked_sentences:
        ranked_sentences[sentence] *= (1 + (random() - 0.5) * 2 * scalar)
        reseed()
    
    return ranked_sentences
    

    
def rank(sentences_to_rank:set[str], all_sentences:set[str]=set()) -> dict[str, float]:
    # PRE-PROCESSING
    G = Graph()

    # 1. Construct all nodes, one node per sentence
    for sentence in sentences_to_rank:
        G.add_node(sentence)



    # 2. Construct all edges, one edge per word
    # Edges are undirected, but will be converted
    # to directed by the PageRank library (later)
    for sentence in sentences_to_rank:
        for word in re.split(r"\s+|-", sentence):
            word = re.sub(r"[^\w█']", '', word).lower()

            if not word or word in stopwords or '█' in word:
                continue

            for node in G:
                if word in node.lower():
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
        
    ranked_sentences = rank(sentences)
    ranked_sentences = randomize_const(ranked_sentences, 0.1)
    important_sentences = select(ranked_sentences, 5)

    for i, sentence in enumerate(important_sentences):
        print(f"SENTENCE {i + 1} IS THE SENTENCE \"{sentence}\"")

if __name__ == "__main__":
    main()