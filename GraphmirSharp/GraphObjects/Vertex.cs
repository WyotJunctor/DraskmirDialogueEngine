namespace Graphmir.GraphObjects {

    public class QueryResponse {}
    public enum QueryTargetType { TgtVertex, RefVert }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex localIndex;

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
        }


        // delete edge how do you index? you already have the source and target vertex:
        // remove ref vert from local map and update in source and target vertex.
        // propagate labels if necessary
        // 
        // unknownRelationship.QueryNeighborhood(QueryTargetType.Vertex, asLabel:true, outgoing:false, refVertLabels:{"Is"})
        // get ref vert label, traverse to ref verts, traverse to edges, 
        public T QueryNeighborhood<T>(
            QueryTargetType queryTargetType,
            bool asLabel = false, 
            bool outgoing = true,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null) 
        where T : QueryResponse {
            return (T)new QueryResponse();
        }
    }
}