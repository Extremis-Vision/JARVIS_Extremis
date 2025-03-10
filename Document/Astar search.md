# Astar search :
### Tags :
#Cour #TZ20 #Formation #informatique #AI #IA 

## Description:
A* search is a heuristic search algorithm that expands the node with the lowest value of \( g(n) + h(n) \).
- **\( g(n) \)**: Cost to reach node \( n \)
- **\( h(n) \)**: Estimated cost to reach the goal from node \( n \)

## Optimality Conditions:
The A* search algorithm is optimal if:
- \( h(n) \) is admissible (never overestimates the true cost)
- \( h(n) \) is consistent (for every node \( n \) and successor \( n' \) with step cost \( c \), \( h(n) \leq h(n') + c \))

The better the heuristic, the better the result.