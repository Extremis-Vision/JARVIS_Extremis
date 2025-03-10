# Minimax:
### Tags :
#Cour #TZ20 #Formation #informatique #AI #IA

Minimax is used for deterministic games where two players are playing optimally. It calculates the optimal moves by considering both maximizing and minimizing player's strategies.

#### Key Elements:
- **Max (X)**: Maximize the score
- **Min (O)**: Minimize the score
- **S0**: Initial state
- **PLAYER(s)**: Identifies which player should move in state \( s \)
- **ACTIONS(s)**: Returns legal moves from state \( s \)
- **RESULT(s,a)**: Returns the state after action \( a \) is taken in state \( s \)
- **TERMINAL(s)**: Checks if state \( s \) is terminal
- **UTILITY(s)**: Final numerical value for a terminal state \( s \)

### Functions:
```python
def MAX_VALUE(state):
    if TERMINAL(state):
        return UTILITY(state)
    v = -INFINITY  # Initialize with the lowest possible value
    for action in ACTIONS(state):
        v = max(v, MIN_VALUE(RESULT(state, action)))
    return v

def MIN_VALUE(state):
    if TERMINAL(state):
        return UTILITY(state)
    v = INFINITY  # Initialize with the highest possible value
    for action in ACTIONS(state):
        v = min(v, MAX_VALUE(RESULT(state, action)))
    return v
```

### How It Works:
- For a given state \( s \), **MAX** picks an action \( a \) that produces the highest value of Min-Value (by considering what **MIN** would pick).
- Conversely, for a given state \( s \), **MIN** picks an action \( a \) that produces the lowest value of Max-Value (by considering what **MAX** would pick).

### Conclusion:
Minimax is optimal in deterministic games but can be computationally expensive. For larger and more complex games, optimization techniques like alpha-beta pruning should be considered to enhance performance.