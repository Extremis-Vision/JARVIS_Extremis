# Search
### Tags :
#Cour #TZ20 #Formation #informatique #AI #IA 

## OverviewIdeal :
- objective = optimal solution 

### Key Components :
- **Initial State**: The starting point or configuration.
- **[[action_ai|actions]] **
- **[[transition model ]]**
- **[[goal test ]]**
- **[[path cost]] function **

## Agent:

The agent perceives its environment and acts upon it, aiming to find an optimal sequence of actions leading to a goal state.

## State Space:

This represents all possible configurations or states that can be reached from the initial state through any sequence of actions. It is often visualized as a graph with nodes (states) and edges (transitions).

### Node : 
Is a data structure that keeps track of 
- **[[state|State]] **
-  **[[parent|Parent]]** 
- **[[action_ai|Action]]**
- **[[path cost|Path Cost]]**

## Search Approach : 
### 1. Basic
- start with a frontier that contain the initial state. 
- start with an empty explored set
- Repeat : 
	- If frontier is empty, then no solution 
	- Remove a node from the frontier 
	- if node contains goal state, return solution 
	- add node to explored set 
	- Expand node, add resulting nodes to the frontier if they aren't already in the frontier or the explored set. 

### 2. [[Uninformed Search]]

### 3. [[Informed Search ]]

### 4. [[Adversarial Search]] :
#### - [[Minimax]]


### Example Search Problems:

#### 1. Puzzle (e.g., 8-Puzzle):
A puzzle involves arranging tiles in a specific configuration, often represented as a grid with empty spaces.

#### 2. Maze:
Finding the shortest path from an entrance to an exit in a maze.

#### 3. Driving Directions:
Determining the optimal route for navigation from one point to another, taking into account obstacles and road conditions.

#### 4. Decision Making:
Choosing the best action among several options based on predefined criteria or preferences.

#### 5. Rational Decision Making:
Making decisions that maximize utility under uncertainty by considering all possible outcomes and their probabilities.