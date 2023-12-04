namespace Graphmir.GraphObjects {
    public class Edge<T> where T : class? {

        public T src = null, tgt = null, refVert = null;

        public Edge(T src, T tgt, T refVert) 
        {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }

        public Edge() {}

        public override int GetHashCode()
        {
            return (src, tgt, refVert).GetHashCode();
        }

        public override bool Equals(object? obj)
        {
            return obj is Edge<T> edge &&
                this.src == edge.src &&
                this.tgt == edge.tgt &&
                this.refVert == edge.refVert;
        }
    }

    public class EdgeUpdate : Edge<Vertex> {
        public QueryTargetType queryTargetType;
        bool add;
        public Vertex invRefVert;

        public EdgeUpdate(Vertex src, Vertex tgt, Vertex refVert, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : base(src, tgt, refVert) {
            this.invRefVert = invRefVert;
            this.queryTargetType = queryTargetType;
            this.add = add;
        }

        public EdgeUpdate(Edge<Vertex> edge, QueryTargetType queryTargetType, bool add) : this(edge, null, queryTargetType, add) {}

        public EdgeUpdate(Edge<Vertex> edge, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : this(edge.src, edge.tgt, edge.refVert, invRefVert, queryTargetType, add) {}

        public EdgeUpdate(Vertex refVert, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : this(null, null, refVert, invRefVert, queryTargetType, add) {}

        public override int GetHashCode()
        {
            return (src, tgt, refVert, queryTargetType).GetHashCode();
        }
    }
}

