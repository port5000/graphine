#! /usr/bin/env python3

"""
base.py

Written by Geremy Condra

Licensed under the GNU GPLv3

Released 25 Mar 2009

This module contains Graphine's base graph represenatation.

The goal of Graph is to provide a flexible, easy to use,
somewhat fast graph implementation. It should be seen as
a firm foundation for later extension, providing all the
tools a developer needs to create the appropriate data
structure for their task with only slight modification.

Interface summary:

To create a new Graph:

	>>> from graph.base import Graph
	>>> # I need named nodes and weighted edges
	>>> g = Graph(["name"], ["weight"])

To add nodes:

	>>> node_1 = g.add_node(name="bob")
	>>> node_2 = g.add_node(name="agamemnon")

To add edges:

	>>> edge_1 = g.add_edge(node_1, node_2, weight=5)

Note that what you're getting back isn't a full
node or edge, eg:

	>>> node_1
	1
	>>> node_2
	2
	>>> edge_1
	-1

As you can see, its just an id used to uniquely
identify it to the graph. To get the full object,
just ask nicely:

	>>> g[node_1]
	Node(name="bob")

The same thing works for edges:

	>>> g[edge_1]
	Edge(start=1, end=2, weight=5)

Notice again that it uses those uids as reference
points. Don't forget them!

To iterate over all the nodes in a graph:

	>>> for node in g.get_nodes():
	>>>	print(node)
	Node(name="bob")
	Node(name="agamemnon")

And, for edges:

	>>> for edge in g.get_edges():
	>>> 	print(edge)
	Edge(start=1, end=2, weight=5)

Of course, if you want to get the uids, just use get_node_uids
or get_edge_uids.

Traversals are just as simple:

	>>> for node_uid in g.depth_first_traversal(node_1):
	>>> 	print(g[node_uid])
	Node(name="bob")
	Node(name="agamemnon")

and similar for depth first traversals. 
"""

# Copyright (C) 2009 Geremy Condra
#
# This file is part of Graphine.
# 
# Graphine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Graphine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Graphine.  If not, see <http://www.gnu.org/licenses/>.


from collections import deque, defaultdict, namedtuple
from weakref import WeakValueDictionary


class Graph(object):
	"""Base class for all Graph mixins"""

	required_node_properties = tuple()
	required_edge_properties = ("start", "end")

	def __init__(self, node_properties, edge_properties):
		"""Base initializer for Graphs.

		To build a new Graph, just instantiate this with
		the properties you want your Nodes and Edges to
		have, eg, if I want named nodes and weighted edges:
		
		>>> g = Graph(["name"], ["weight"])
	
		I used a list here, but any iterable will suffice,
		including dictionaries.
		"""
		# add required attributes to edges
		node_properties = self.required_node_properties + tuple(node_properties)
		edge_properties = self.required_edge_properties + tuple(edge_properties)
		# instantiate node and edge classes
		self.Node = namedtuple("Node", node_properties)
		self.Edge = namedtuple("Edge", edge_properties)
		# keep track of relevant properties
		self.nodes = {}
		self.edges = {}
		# keep track of all adjacencies via start -> edge_uid mappings
		self.adjacency_list = defaultdict(set)
		# and of the available uid's
		self.unused_node_uids = deque()		# these are positive
		self.unused_edge_uids = deque()		# these are negative

	def __contains__(self, element):
		"""returns True if the element is a member of the graph"""
		#XXX ugly way to tell- is there a better one?
		if element.__class__.__name__ == "Node":
			return element in self.nodes.values()
		else:
			return element in self.edges.values()

	def __getitem__(self, uid):
		"""retrieves the item corresponding to the given uid"""
		if uid > 0:
			return self.nodes[uid]
		else:
			return self.edges[uid]

	def __setitem__(self, uid, value):
		"""sets the value corresponding to the given uid"""
		# if its a node
		if uid > 0:
			self.nodes[uid] = value
		else:
			e = self.edges[uid]
			if e.start is value.start:
				self.edges[uid] = value
			else:
				# disconnect the edge
				self.adjacency_list[e.start].remove(uid)
				# and reconnect it
				self.adjacency_list[value.start].add(uid)

	def __delitem__(self, uid):
		"""deletes the item corresponding to the given uid"""
		# if its a node
		if uid > 0:
			return self.remove_node(uid)
		else:
			return self.remove_edge(uid)

	def get_node_uid(self):
		"""gets a natural number uid for a new node"""
		try:
			return self.unused_node_uids.pop()
		except:
			return len(self.nodes) + 1

	def get_edge_uid(self):
		"""gets an integral uid for a new edge"""
		try:
			return self.unused_edge_uids.pop()
		except:
			return -len(self.edges) - 1

	def node_uids(self):
		"""Iterates over all node uids"""
		for uid in self.nodes:
			yield uid

	def edge_uids(self):
		"""Iterates over all edge uids"""
		for uid in self.edges:
			yield uid

	def add_node(self, **kwargs):
		"""Adds a node to the current graph.

		kwargs should include all the fields required to
		instantiate your Node class, eg:
		
		>>> g = Graph(["name"], [])
		>>> g.add_node(name="bob")

		Giving fewer, more, or differently named fields
		will throw a TypeError.
		"""
		uid = self.get_node_uid()
		self.nodes[uid] = self.Node(**kwargs)
		return uid

	def add_edge(self, start, end, **kwargs):
		"""Adds an edge to the current graph.

		The same notes on adding nodes apply here,
		eg, make sure that you provide a value for
		all the properties in your Edge.
		"""
		uid = self.get_edge_uid()
		e = self.Edge(start=start, end=end, **kwargs)
		self.edges[uid] = e
		self.adjacency_list[start].add(uid)
		return uid

	def modify_node(self, uid, **kwargs):
		"""Modifies an existing node.
		
		Essentially, this does a dictionary update on the
		node. Note that you can't add or remove attributes 
		this way, just set their values, eg:

		>>> bill = g.add_node(name="bill")
		>>> bob = g.modify_node(name="bob")
		>>> # bill and bob are uid's, not Nodes
		>>> bill is bob
		True
		>>> g[bob]
		Node(name="bob")
		>>> g[bill]
		Node(name="bob")
		>>> # trying to turn bob evil...
		>>> g.modify_node(bob, mustache=True)
		...stack trace...
		ValueError: Got unexpected field names: ...

		"""
		n = self[uid]
		n = n._replace(**kwargs)
		self[uid] = n
		return uid

	def modify_edge(self, uid, **kwargs):
		"""Modifies an existing edge.

		See the notes on modify_edges for more information.
		"""
		old_edge = self[uid]
		e = old_edge._replace(**kwargs)
		self[uid] = e
		if old_edge.start != e.start:
			self.adjacency_list[old_edge.start].remove(uid)
			self.adjacency_list[e.start].add(uid)
		return uid

	def remove_node(self, uid):
		"""Removes a node from the graph.

		Note that this does not remove the edges that
		had this node as a terminus, it simply removes
		them from the adjacency listing. It is up
		to the programmer to ensure that bad things
		don't happen:

		>>> # ok...
		>>> bob = g.add_node(name="bob")
		>>> bill = g.add_node(name="bill")
		>>> e = g.add_edge(bob, bill)
		>>> g.remove_node(bill)
		2
		>>> # still ok...
		>>> for node in g.get_adjacent_nodes(bob):
		>>> 	print(node)
		>>>
		>>> # BADBADBAD
		>>> for edge in g.search_edges(start=bob, end=bill):
		>>>	print(edge)
		Edge(start=1, end=2)
		>>>

		"""
		# remove it from node storage
		n = self.nodes.pop(uid)
		# remove it from adjacency tracking
		try:
			del self.adjacency_list[uid]
		except:
			pass
		# add it to the untracked uids
		self.unused_node_uids.append(uid)
		# pass it back to the caller
		return n

	def remove_edge(self, uid):
		"""Removes an edge from the graph"""
		# remove it from edge storage
		e = self.edges.pop(uid)
		# remove it from adjacency tracking
		self.adjacency_list[e.start].remove(uid)
		# add it to the untracked uids
		self.unused_edge_uids.append(uid)
		# pass it back to the caller
		return e

	def get_nodes(self):
		"""Iterates over all the nodes."""
		for node in self.nodes.values():
			yield node

	def get_edges(self):
		"""Iterates over all the edges."""
		for edge in self.edges.values():
			yield edge

	def search_nodes(self, **kwargs):
		"""Convenience function to get nodes based on some properties.

		Example:
		
		>>> g = Graph(["name"], [])
		>>> jim = g.add_node(name="jim")
		>>> bob = g.add_node(name="bob")
		>>> for node in g.search_nodes(name="jim"):
		>>> 	print(node)
		Node(name="jim")
		>>>

		"""
		for node in self.get_nodes():
			for k, v in kwargs.items():
				if not v == getattr(node, k):
						continue
				yield node

	def search_edges(self, **kwargs):
		"""Convenience function to get edges based on some properties.

		Works identically to search_nodes.
		"""
		for node in self.get_edges():
			for k, v in kwargs.items():
				if not v == getattr(node, k):
					continue
				yield node

	def get_adjacent_uids(self, uid):
		"""Convenience function to get uids based on adjacency."""
		yield uid
		for edge_uid in self.adjacency_list.get(uid, set()):
			yield self[edge_uid].end

	def get_adjacent_nodes(self, uid):
		"""Returns the nodes which are adjacent to the given uid."""
		for uid in self.get_adjacent_uids(uid):
			yield self[uid]

	def get_outgoing_uids(self, uid):
		"""Convenience function to get uids based on incidence."""
		for uid in self.adjacency_list(uid):
			yield uid

	def get_outgoing_edges(self, uid):
		"""Gets all the outgoing edges for the given node."""
		for uid in self.get_outgoing_uids(uid):
			yield self[uid]

	def a_star_traversal(self, root_uid, selector):
		"""Traverses the graph using selector as a selection filter on the unvisited nodes."""
		unvisited = deque()
		visited = deque()
		unvisited.append(root_uid)
		while unvisited:
			next_uid = selector(unvisited)
			yield next_uid
			visited.append(next_uid)
			for uid in self.get_adjacent_uids(next_uid):
				if uid not in unvisited:
					if uid not in visited:
						unvisited.append(uid)

	def depth_first_traversal(self, root):
		"""Traverses the graph by visiting a node, then a child of that node, and so on."""
		for node in self.a_star_traversal(root, lambda s: s.pop()):
			yield node
		
	def breadth_first_traversal(self, root):
		"""Traverses the graph by visiting a node, then each of its children, then their children"""
		for node in self.a_star_traversal(root, lambda s: s.popleft()):
			yield node

	def generate_subgraph(self, *nodes):
		"""Generate a subgraph that includes only the given nodes and the edges between them."""
		# get the properties of Nodes and Edges
		node_properties = set(self.Node._fields) - set(self.required_node_properties)
		edge_properties = set(self.Edge._fields) - set(self.required_edge_properties)
		# instantiate the new graph
		g = type(self)(node_properties, edge_properties)
		# add all the nodes to the new graph
		for node in nodes:
			n = self[node]._asdict()
			properties = dict()
			for attr in n:
				if attr in node_properties:
					properties[attr] = n[attr]
			g.add_node(**properties)
		# find all the edges 
		node_set = set(nodes)
		for node in node_set:
			for edge_id in self.adjacency_list[node]:
				e = self[edge_id]._asdict()
				properties = dict()
				for attr in e:
					if attr in edge_properties:
						properties[attr] = e[attr]
				if e["start"] in node_set:
					if e["end"] in node_set:
						g.add_edge(e["start"], e["end"], **properties)
		return g

	def size(self):
		"""Reports the number of edges in the graph"""
		return len(self.edges)

	def order(self):
		"""Reports the number of nodes in the graph"""
		return len(self.nodes)
