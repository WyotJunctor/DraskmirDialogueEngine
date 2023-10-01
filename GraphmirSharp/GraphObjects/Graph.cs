namespace Graphmir.GraphObjects {
    public class Graph {

        struct RealizedMessage {
            public HashSet<Vertex> AddVerts, DelVerts;
            public HashSet<Edge> AddEdges, DelEdges;
        }

        public Dictionary<Label, Vertex> Vertices = new Dictionary<Label, Vertex>();

        RealizedMessage Realize() {
            return new RealizedMessage();
        }

    }
}