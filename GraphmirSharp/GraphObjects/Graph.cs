namespace Graphmir.GraphObjects {
    public class Graph {

        struct RealizedMessage {
            public HashSet<Vertex> AddVerts, DelVerts;
            public HashSet<Edge> AddEdges, DelEdges;
        }

        struct RefVertContainer {
            public Vertex refVert;
            public Vertex invRefVert;

            public RefVertContainer (Vertex refVert, Vertex invRefVert) {
                this.refVert = refVert;
                this.invRefVert = invRefVert;
            }
        }

        public struct MessageResponse {
            public UpdateRecord updateRecord = new UpdateRecord();
            public Dictionary<Vertex, HashSet<Label>> labelAddMap = new Dictionary<Vertex, HashSet<Label>>();
            public Dictionary<Vertex, HashSet<Label>> labelDelMap = new Dictionary<Vertex, HashSet<Label>>();

            public MessageResponse() {}
        }

        (HashSet<Edge> primaryEdges, HashSet<Edge> secondaryEdges) SplitEdges(HashSet<Edge> edges) {
            return new (new HashSet<Edge>(), new HashSet<Edge>());
        }

        public Dictionary<Label, Vertex> vertices = new Dictionary<Label, Vertex>();

        RealizedMessage Realize(GraphMessage message) {
            return new RealizedMessage();
        }

        public MessageResponse UpdateFrom(GraphMessage message) {
            RealizedMessage realizedMessage = Realize(message);
            MessageResponse response = new MessageResponse();

            var delPrimaryEdges = realizedMessage.DelEdges;
            var delSecondaryEdges = realizedMessage.DelEdges;
            var delInvRefVerts = new HashSet<RefVertContainer>();

            foreach (var vert in realizedMessage.DelVerts) {
                // remove from Graph
                vertices.Remove(vert.vLabel);
                // get all outgoing and ingoing edges
                // split em up
                // add to delPrimaryEdges and delSecondaryEdges
                (HashSet<Edge> pEdges, HashSet<Edge> sEdges) = SplitEdges(vert.GetEdges(EdgeDirection.Undirected));
                delPrimaryEdges.UnionWith(pEdges);
                delSecondaryEdges.UnionWith(sEdges);
                // add invRefVerts to delInvRefVerts
                // get tuples of (invRefVert, refVert)
                foreach (var invRefVert in vert.GetInvRefVerts()) {
                    delInvRefVerts.Add(new RefVertContainer(vert, invRefVert));
                }
            }

            // handle del invRefVerts
            foreach (var refVertContainer in delInvRefVerts) {
                // this is the src vert,
                (HashSet<Edge> pEdges, HashSet<Edge> sEdges) = SplitEdges(
                    refVertContainer.refVert.QueryNeighborhood<Edge>(
                        QueryTargetType.Edge,
                        dir:EdgeDirection.Undirected,
                        refVertLabels:new HashSet<Label>() {refVertContainer.refVert.vLabel}));
                // add all edges to delPrimary/Secondary edges
                delPrimaryEdges.UnionWith(pEdges);
                delSecondaryEdges.UnionWith(sEdges);
            }
            
            /*
        public HashSet<T> QueryNeighborhood<T>(
            QueryTargetType queryTargetType,
            bool asLabel = false, 
            bool outgoing = true,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null) 
            */

            foreach (var edge in delPrimaryEdges) {
            }
            // handle deleted primary edges
            //  src vert, if not deleted
            //      update local index with removed refVert, tgt tuples
            //          remove edge between tgtVert and refVert
            //  if tgt vert not deleted
            //      remove edge from tgt vert local index, freebie
            //  this results in some loss of labels
            //  propagate
            //  update realizedMessage.labelDelMap;
            // include refVerts in the dependency calculation
            //  when updating labels, tell invRefVerts

            // handle deleted secondary edges
            // we do this before added primary edges because 
            // it would be dumb to add labels and then immediately remove them
            // just remove the refVert, tgtVert edge in local index
            // if refVert edgetype, then propagate label changes

            // handle added verts
            // just add it to the dictionary

            // handle added primary edges
            //  update local index of src and tgt vert
            // propagate,
            // include refVerts in the dependency calculation
            // when all of a vertex's dependencies have been handled
            // it should propagate labels to neighbors
            // propagate labels to invRefVert

            // handle added secondary edges
            // just add refVert, tgtVert edge in local index long with labels

            // ref vert label changes. I guess these label changes can propagate immediately

            return response;
        }

    }
}