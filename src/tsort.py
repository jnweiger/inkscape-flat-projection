#! /usr/bin/python3
#

from __future__ import print_function
from collections import defaultdict     # minimum python 2.5

class TSort:
    """
    Kahn's Algorithm for topological ordering
    FROM: https://www.geeksforgeeks.org/topological-sorting-indegree-based-solution/
    """

    def __init__(self, vertices):
        self.graph = defaultdict(list)  # dictionary of adjacency List
        self.V = vertices               # No. of vertices

    def addPre(self, u, v):
        self.graph[u].append(v)

    def sort(self):
        # Create a vector to store indegrees of all vertices.
        # Initialize all indegrees as 0.
        in_degree = [0]*(self.V)

        # Traverse adjacency lists to fill indegrees of vertices.
        # This step takes O(V+E) time
        for i in self.graph:
            for j in self.graph[i]:
                in_degree[j] += 1

        # Create an queue and enqueue all vertices with indegree 0
        queue = []
        for i in range(self.V):
            if in_degree[i] == 0:
                queue.append(i)

        #Initialize count of visited vertices
        cnt = 0

        # Create a vector to store result (A topological ordering of the vertices)
        top_order = []

        # One by one dequeue vertices from queue and enqueue
        # adjacents if indegree of adjacent becomes 0
        while queue:

            # Extract front of queue (or perform dequeue)
            # and add it to topological order
            u = queue.pop(0)
            top_order.append(u)

            # Iterate through all neighbouring nodes
            # of dequeued node u and decrease their in-degree by 1
            for i in self.graph[u]:
                in_degree[i] -= 1
                # If in-degree becomes zero, add it to queue
                if in_degree[i] == 0:
                    queue.append(i)
            cnt += 1

        # Check if there was a cycle
        if cnt != self.V:
            raise Exception("cyclic dependency")
        return top_order

if __name__ == '__main__':
  k = TSort(6)
  k.addPre(5, 2)
  k.addPre(5, 0)
  k.addPre(4, 0)
  k.addPre(4, 1)
  k.addPre(2, 3)
  k.addPre(3, 1)

  sorted_list = k.sort()
  print("The next two lines should match:\n[4, 5, 2, 0, 3, 1]")
  print(sorted_list)
