namespace Graphmir.GraphObjects {

    public enum QueryTargetType { TgtVertex, RefVert, Edge }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }

    public class LabelDelta {
        public HashSet<Label> addLabels = new HashSet<Label>();
        public HashSet<Label> delLabels = new HashSet<Label>();
    }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex localIndex;

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
        }

        public Vertex(Label vLabel) : this(vLabel, Clock.globalTimestamp) {
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
            // TODO
            return new HashSet<T>();
        }

        public void UpdateNeighborhood() {
            // TODO
            // if labels updated, tell invRefVerts?
        }

        public LabelDelta UpdateLabels() {
            // TODO
            return new LabelDelta();
        }

        public void PropagateLabels() {
            // TODO
        }

        public HashSet<Edge> GetEdges(EdgeDirection dir) {
            // TODO
            return new HashSet<Edge>();
        }

        public HashSet<Vertex> GetInvRefVerts() {
            // TODO
            return new HashSet<Vertex>();
        }

        public HashSet<Vertex> GetDependents() {
            // TODO
            // get childrne via edges and invRefVerts
            return new HashSet<Vertex>();
        }

        public bool IsPrimaryRefVert() {
            // TODO
            return false;
        }
    }
}