namespace Graphmir.GraphObjects {
    public class Edge {

        public Vertex src;
        public Vertex tgt;
        public Vertex refVert;
    
        public Edge(Vertex src, Vertex tgt, Vertex refVert) {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }

        public override int GetHashCode()
        {
            return new {src, tgt, refVert}.GetHashCode();
        }

    }
}