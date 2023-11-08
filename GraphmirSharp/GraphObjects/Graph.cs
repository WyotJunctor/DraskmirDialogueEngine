using System.Collections;



namespace Graphmir.GraphObjects {

    public class MessageResponse {
        public UpdateRecord updateRecord = new UpdateRecord();
        public DefaultDictionary<Vertex, HashSet<Label>> labelAddMap = new DefaultDictionary<Vertex, HashSet<Label>>();
        public DefaultDictionary<Vertex, HashSet<Label>> labelDelMap = new DefaultDictionary<Vertex, HashSet<Label>>();

        public MessageResponse() {}

        public void AddLabelDelta(Vertex vert, LabelDelta labelDelta) {
            labelDelMap[vert].UnionWith(labelDelta.delLabels);
            labelDelMap[vert].ExceptWith(labelDelta.addLabels);
            labelAddMap[vert].UnionWith(labelDelta.addLabels);
        }
    }

    public class Graph {
  
        public Dictionary<Label, Vertex> vertices = new Dictionary<Label, Vertex>();

        class RealizedMessage {
            public HashSet<Vertex> 
                addVerts = new HashSet<Vertex>(), 
                delVerts = new HashSet<Vertex>();
            public HashSet<Edge> 
                addPrimaryEdges = new HashSet<Edge>(), 
                addSecondaryEdges = new HashSet<Edge>(),
                delPrimaryEdges = new HashSet<Edge>(), 
                delSecondaryEdges = new HashSet<Edge>();
        }

        public class DependencyCount {
            public int totalDependencies;
            public int calculatedDependencies;
        }

        (HashSet<Edge> primaryEdges, HashSet<Edge> secondaryEdges) SplitEdges(HashSet<Edge> edges) {
            HashSet<Edge> primaryEdges = new HashSet<Edge>();
            HashSet<Edge> secondaryEdges = new HashSet<Edge>();
            foreach (var edge in edges) {
                if (edge.refVert.IsPrimaryRefVert())
                    primaryEdges.Add(edge);
                else
                    secondaryEdges.Add(edge);
            }
            return new (primaryEdges, secondaryEdges);
        }

        public bool CheckEdgeRef(
            Label vLabel, 
            ref Vertex vertRef, 
            GraphMessage message, 
            Dictionary<Label, Vertex> realizedVerts) {

            if (vertices.ContainsKey(vLabel)) {
                vertRef = vertices[vLabel];
            }
            else if (message != null && message.addVerts.Contains(vLabel)) {
                vertRef = realizedVerts[vLabel];
            }
            else {
                return false;
            }
            return true;
        }

        public Edge RealizeEdge(
            EdgeContainer edge,
            GraphMessage message=null, 
            Dictionary<Label, Vertex> realizedVerts=null) {

            Edge realizedEdge = new Edge();
            CheckEdgeRef(edge.src, ref realizedEdge.src, message, realizedVerts);
            CheckEdgeRef(edge.tgt, ref realizedEdge.tgt, message, realizedVerts);
            CheckEdgeRef(edge.refVert, ref realizedEdge.refVert, message, realizedVerts);

            return realizedEdge;
        }

        RealizedMessage Realize(GraphMessage message) {
            // the graph message is always in a valid state
            // iterate over add vertices, if exists, add to the thing
            RealizedMessage realizedMessage = new RealizedMessage();
            Dictionary<Label, Vertex> realizedVerts = new Dictionary<Label, Vertex>();
            foreach (var vLabel in message.addVerts) {
                if (!vertices.ContainsKey(vLabel)) {
                    var realizedVert = new Vertex(vLabel);
                    realizedMessage.addVerts.Add(realizedVert);
                    realizedVerts[vLabel] = realizedVert;
                }
            }
            // iterate over del vertices, if exists, add to the thing
            foreach (var vLabel in message.delVerts) {
                if (vertices.ContainsKey(vLabel)) {
                    realizedMessage.delVerts.Add(new Vertex(vLabel));
                }
            }
            foreach (var edge in message.addEdges) {
                // check src, tgt, and ref exists in graph or add verts
                var realizedEdge = RealizeEdge(edge, message, realizedVerts);
                if (realizedEdge != null) {
                    if (realizedEdge.refVert.IsPrimaryRefVert()) {
                        realizedMessage.addPrimaryEdges.Add(realizedEdge);
                    }   
                    else {
                        realizedMessage.delPrimaryEdges.Add(realizedEdge);
                    }
                } 
            }
            foreach (var edge in message.delEdges) {
                // check src, tgt, and ref exists in graph or add verts
                var realizedEdge = RealizeEdge(edge);
                if (realizedEdge != null) {
                    if (realizedEdge.refVert.IsPrimaryRefVert()) {
                        realizedMessage.addPrimaryEdges.Add(realizedEdge);
                    }   
                    else {
                        realizedMessage.delPrimaryEdges.Add(realizedEdge);
                    }
                } 
            }
            return realizedMessage;
        }

        void PropagateLabels(
                HashSet<Vertex> sourceVerts,
                Queue<Vertex> queue,
                MessageResponse response) {
            Dictionary<Vertex, DependencyCount> dependencyMap = new Dictionary<Vertex, DependencyCount>();
            while (queue.Count > 0) {
                // pop queue
                Vertex vert = queue.Dequeue();
                // if not in dependency map, add to map
                if (dependencyMap.ContainsKey(vert) == false) {
                    dependencyMap[vert] = new DependencyCount();
                }
                // visit children and invRefVerts
                foreach (var child in vert.GetDependents()) {
                    if (dependencyMap.ContainsKey(child) == false) {
                        dependencyMap[child] = new DependencyCount();
                        queue.Enqueue(child);
                        sourceVerts.Remove(child);
                    }
                    dependencyMap[child].totalDependencies += 1;
                }
            }

            queue = new Queue<Vertex>(sourceVerts);
            // while queue not empty
            while (queue.Count > 0) {
                // pop queue
                Vertex vert = queue.Dequeue();
                foreach (var child in vert.GetDependents()) {
                    if (++dependencyMap[child].calculatedDependencies == dependencyMap[child].totalDependencies) {
                        queue.Enqueue(child);
                    }
                }
                // propagate labels to neighbors if neighbors not deleted?
                // calculate label delta and add to labelMap
                response.AddLabelDelta(vert, vert.UpdateLabels());
                vert.PropagateLabels();
            }
        }

        public MessageResponse UpdateFrom(GraphMessage message) {
            RealizedMessage realizedMessage = Realize(message);
            MessageResponse response = new MessageResponse();

            Queue<Vertex> queue = new Queue<Vertex>();
            HashSet<Vertex> sourceVerts = new HashSet<Vertex>();

            foreach (var vert in realizedMessage.delVerts) {
                // remove from Graph
                vertices.Remove(vert.vLabel);
                // get all outgoing and ingoing edges
                // split em up
                // add to delPrimaryEdges and delSecondaryEdges
                (HashSet<Edge> pEdges, HashSet<Edge> sEdges) = SplitEdges(vert.GetEdges(EdgeDirection.Undirected));
                realizedMessage.delPrimaryEdges.UnionWith(pEdges);
                realizedMessage.delSecondaryEdges.UnionWith(sEdges);
                foreach (var invRefVert in vert.GetInvRefVerts()) {
                    if (realizedMessage.delVerts.Contains(invRefVert) == false) {
                        // TODO* invRefVert.UpdateNeighborhood(delete vert from refVerts);
                        if (vert.IsPrimaryRefVert()) {
                            sourceVerts.Add(invRefVert);
                            queue.Enqueue(invRefVert);
                        }
                    }
                }
            }

            // handle deleted primary edges
            foreach (var edge in realizedMessage.delPrimaryEdges) {
                bool srcExists=false, tgtExists=false;
                if (!realizedMessage.delVerts.Contains(edge.src)) {
                    srcExists = true;
                    // TODO* edge.src.UpdateNeighborhood(delete (edge.refVert, edge.tgt) from local index);
                    // update response.labelDelMap
                    // add to source verts
                    sourceVerts.Add(edge.src);
                    queue.Enqueue(edge.src);
                }
                if (!realizedMessage.delVerts.Contains(edge.tgt)) {
                    tgtExists = true;
                    // TODO* edge.tgt.UpdateNeighborhood(delete (edgeRefVert, edge.src) from local index);
                }
                if (srcExists || tgtExists) {
                    response.updateRecord.AddEdge(edge, false);
                }
            }
            PropagateLabels(sourceVerts, queue, response);

            // handle deleted secondary edges
            // we do this before added primary edges because 
            // it would be dumb to add labels and then immediately remove them
            foreach (var edge in realizedMessage.delSecondaryEdges) {
                // just remove the refVert, tgtVert edge in local index 
                // TODO* edge.src.UpdateNeighborhood(delete (refVert, edge.tgt) from local index)
                // TODO* edge.tgt.UpdateNeighborhood(delete (refVert, edge.src) from local index)
            }

            // handle added verts
            foreach (var vert in realizedMessage.addVerts) {
                // just add it to the dictionary
                vertices[vert.vLabel] = vert;
                // add label
                response.labelAddMap[vert].Add(vert.vLabel);
            }

            queue = new Queue<Vertex>();
            // handle added primary edges
            foreach (var edge in realizedMessage.addPrimaryEdges) {
                // update local index of src and tgt vert
                // TODO* edge.src.UpdateNeighborhood(add (refVert, edge.tgt) to local index);
                sourceVerts.Add(edge.src);
                queue.Enqueue(edge.src);
                // TODO* edge.tgt.UpdateNeighborhood(add (refVert, edge.src) to local index);
            }
            // propagate,
            PropagateLabels(sourceVerts, queue, response);

            // handle added secondary edges
            foreach (var edge in realizedMessage.addSecondaryEdges) {
                // just add refVert, tgtVert edge in local index long with labels
                // TODO* edge.src.UpdateNeighborhood(add (refVert, edge.tgt) to local index)
                // TODO* edge.tgt.UpdateNeighborhood(add (refVert, edge.src) to local index)
            }

            return response;
        }
    }
}