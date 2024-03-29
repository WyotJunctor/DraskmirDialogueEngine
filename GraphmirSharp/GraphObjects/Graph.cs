using System.Collections;

namespace Graphmir.GraphObjects {

    public class MessageResponse {
        public UpdateRecord updateRecord = new UpdateRecord();
        public DefaultDictionary<Vertex, EdgeMap<Label, Label>> labelAddMap = new DefaultDictionary<Vertex, EdgeMap<Label, Label>>();
        public DefaultDictionary<Vertex, EdgeMap<Label, Label>> labelDelMap = new DefaultDictionary<Vertex, EdgeMap<Label, Label>>();

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
            public HashSet<Edge<Vertex>>
                addPrimaryEdges = new HashSet<Edge<Vertex>>(),
                addSecondaryEdges = new HashSet<Edge<Vertex>>(),
                delPrimaryEdges = new HashSet<Edge<Vertex>>(),
                delSecondaryEdges = new HashSet<Edge<Vertex>>();
        }

        public class DependencyCount {
            public int totalDependencies;
            public int calculatedDependencies;
        }

        (HashSet<Edge<Vertex>> primaryEdges, HashSet<Edge<Vertex>> secondaryEdges) SplitEdges(HashSet<Edge<Vertex>> edges) {
            HashSet<Edge<Vertex>> primaryEdges = new HashSet<Edge<Vertex>>();
            HashSet<Edge<Vertex>> secondaryEdges = new HashSet<Edge<Vertex>>();
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

        public Edge<Vertex> RealizeEdge(
            Edge<Label> edge,
            GraphMessage message=null,
            Dictionary<Label, Vertex> realizedVerts=null) {

            Edge<Vertex> realizedEdge = new Edge<Vertex>();
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

            // iterate over del vertices, if exists, add to the thing
            foreach (var vLabel in message.delVerts) {
                if (vertices.ContainsKey(vLabel)) {
                    realizedMessage.delVerts.Add(new Vertex(vLabel));
                }
                else if (message.addVerts.Contains(vLabel)) {
                    message.addVerts.Remove(vLabel);
                }
            }

            foreach (var vLabel in message.addVerts) {
                if (!vertices.ContainsKey(vLabel)) {
                    var realizedVert = new Vertex(vLabel);
                    realizedMessage.addVerts.Add(realizedVert);
                    realizedVerts[vLabel] = realizedVert;
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
                else if (message.addEdges.Contains(edge)) {
                    message.addEdges.Remove(edge);
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
                (HashSet<Edge<Vertex>> pEdges, HashSet<Edge<Vertex>> sEdges) = SplitEdges(vert.GetEdges(EdgeDirection.Undirected));
                realizedMessage.delPrimaryEdges.UnionWith(pEdges);
                realizedMessage.delSecondaryEdges.UnionWith(sEdges);
                // get the vertices in which 'vert' appears as a refVert and delete the refVert
                foreach (var invRefVert in vert.GetInvRefVerts()) {
                    if (realizedMessage.delVerts.Contains(invRefVert) == false) {
                        invRefVert.DeleteRefVert(vert);
                        // add to UpdateRecord
                        response.updateRecord.AddEdge(new EdgeUpdate(vert, invRefVert, QueryTargetType.RefVert, false));
                        if (vert.IsPrimaryRefVert()) {
                            sourceVerts.Add(invRefVert);
                            queue.Enqueue(invRefVert);
                        }
                    }
                }
            }

            // handle deleted primary edges
            foreach (var edge in realizedMessage.delPrimaryEdges) {
                if (!realizedMessage.delVerts.Contains(edge.src)) {
                    edge.src.DeleteEdge(edge, EdgeDirection.Outgoing);
                    // add to source verts
                    sourceVerts.Add(edge.src);
                    queue.Enqueue(edge.src);
                }
                if (!realizedMessage.delVerts.Contains(edge.tgt)) {
                    edge.tgt.DeleteEdge(edge, EdgeDirection.Ingoing);
                }
                // add to update record
                response.updateRecord.AddEdge(new EdgeUpdate(edge, QueryTargetType.Edge, false));
            }
            PropagateLabels(sourceVerts, queue, response);

            // handle deleted secondary edges
            // we do this before added primary edges because
            // it would be dumb to add labels and then immediately remove them
            foreach (var edge in realizedMessage.delSecondaryEdges) {
                // just remove the refVert, tgtVert edge in local index
                edge.src.DeleteEdge(edge, EdgeDirection.Outgoing);
                edge.tgt.DeleteEdge(edge, EdgeDirection.Ingoing);
                // add to update record
                response.updateRecord.AddEdge(new EdgeUpdate(edge, QueryTargetType.Edge, false));
            }

            // handle added verts
            foreach (var vert in realizedMessage.addVerts) {
                // just add it to the dictionary
                vertices[vert.vLabel] = vert;
                // add label
                response.labelAddMap[vert] = new EdgeMap<Label, Label>();
                response.labelAddMap[vert].Add(vert.vLabel, EngineConfig.primaryLabel);
            }

            queue = new Queue<Vertex>();
            sourceVerts = new HashSet<Vertex>();
            // handle added primary edges
            foreach (var edge in realizedMessage.addPrimaryEdges) {
                // update local index of src and tgt vert
                edge.src.AddEdge(edge, EdgeDirection.Outgoing);
                sourceVerts.Add(edge.src);
                queue.Enqueue(edge.src);
                edge.tgt.AddEdge(edge, EdgeDirection.Ingoing);
                // add to update record
                response.updateRecord.AddEdge(new EdgeUpdate(edge, QueryTargetType.Edge, true));
            }
            // propagate,
            PropagateLabels(sourceVerts, queue, response);

            // handle added secondary edges
            foreach (var edge in realizedMessage.addSecondaryEdges) {
                // just add refVert, tgtVert edge in local index long with labels
                edge.src.AddEdge(edge, EdgeDirection.Outgoing);
                edge.tgt.AddEdge(edge, EdgeDirection.Ingoing);
                // add to update record
                response.updateRecord.AddEdge(new EdgeUpdate(edge, QueryTargetType.Edge, true));
            }

            return response;
        }
    }
}