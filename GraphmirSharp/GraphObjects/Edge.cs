namespace Graphmir.GraphObjects {
    public class Edge {

        public Vertex src;
        public Vertex tgt;
        public Vertex refVert;
        public uint LastUpdated;
    
        public Edge(Vertex src, Vertex tgt, Vertex refVert, uint lastUpdated) {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
            this.LastUpdated = lastUpdated;
        }
    }
}