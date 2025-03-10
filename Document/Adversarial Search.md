# Adversarial Search
### Tags :
#Cour #TZ20 #Formation #informatique #AI #IA 

## Summary :
- Fighting against an adversary.

## [[Minimax]] 
Is the foundation of adversarial search for deterministic games, optimizing player decisions to maximize or minimize their respective scores.

## How can we do better ? / Optimisation :

### Alpha-beta Pruning:
Alpha-beta pruning is an optimization technique for minimax that reduces the number of nodes evaluated by eliminating branches that cannot affect the final decision.
- **Alpha (\(\alpha\))**: The best value for the maximizing player in the current branch
- **Beta (\(\beta\))**: The best value for the minimizing player in the current branch

### Depth-Limited [[Minimax]]:
Depth-limited minimax is an optimization technique where we limit the depth of the search tree to a given maximum depth \( d \).
- Helps prevent infinite recursion when dealing with very large state spaces.

### Evaluation function :
A function that estimates the expected utility of the game from a given state. The performance of this function can significantly impact the effectiveness of the algorithm.
```python
def EVALUATE_STATE(state):
    # Implement your heuristic or model to estimate the utility
    return estimated_utility
```