namespace Graphmir.GraphObjects {
    public class Edge {

        public Vertex src = null;
        public Vertex tgt = null;
        public Vertex refVert = null;
    
        public Edge(Vertex src, Vertex tgt, Vertex refVert) {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }

        public Edge() {}

        public override int GetHashCode()
        {
            return new {src, tgt, refVert}.GetHashCode();
        }

    }
}