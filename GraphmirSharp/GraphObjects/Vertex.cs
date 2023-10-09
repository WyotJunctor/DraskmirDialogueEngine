namespace Graphmir.GraphObjects {

    public enum QueryTargetType { TgtVertex, RefVert, Edge }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex localIndex;

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
        }


        public HashSet<Label> GetLabels() {
            return new HashSet<Label>();
        }

        // delete edge how do you index? you already have the source and target vertex:
        // remove ref vert from local map and update in source and target vertex.
        // propagate labels if necessary
        // 
        // unknownRelationship.QueryNeighborhood(QueryTargetType.Vertex, asLabel:true, outgoing:false, refVertLabels:{"Is"})
        // get ref vert label, traverse to ref verts, traverse to edges, 
        public HashSet<T> QueryNeighborhood<T>(
            QueryTargetType queryTargetType,
            bool asLabel = false, 
            EdgeDirection dir = EdgeDirection.Outgoing,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null) 
        {
            return new HashSet<T>();
        }

        public HashSet<Edge> GetEdges(EdgeDirection dir) {
            return new HashSet<Edge>();
        }

        public HashSet<Vertex> GetInvRefVerts() {
            return new HashSet<Vertex>();
        }
    }
}