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

    public class EdgeContainer {
        public Label src, tgt, refVert;

        public EdgeContainer(Label src, Label tgt, Label refVert)
        {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }

        public override bool Equals(object? obj)
        {
            return obj is EdgeContainer edge &&
                this.src == edge.src &&
                this.tgt == edge.tgt &&
                this.refVert == edge.refVert;
        }

        public override int GetHashCode()
        {
            return (this.src, this.tgt, this.refVert).GetHashCode();
        }
    }

    public class EdgeUpdate : Edge {
        public QueryTargetType queryTargetType;
        bool add;
        public Vertex invRefVert;

        public EdgeUpdate(Vertex src, Vertex tgt, Vertex refVert, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : base(src, tgt, refVert) {
            this.invRefVert = invRefVert;
            this.queryTargetType = queryTargetType;
            this.add = add;
        }

        public EdgeUpdate(Edge edge, QueryTargetType queryTargetType, bool add) : this(edge, null, queryTargetType, add) {}

        public EdgeUpdate(Edge edge, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : this(edge.src, edge.tgt, edge.refVert, invRefVert, queryTargetType, add) {}

        public EdgeUpdate(Vertex refVert, Vertex invRefVert, QueryTargetType queryTargetType, bool add) : this(null, null, refVert, invRefVert, queryTargetType, add) {}

        public override int GetHashCode()
        {
            return (src, tgt, refVert, queryTargetType).GetHashCode();
        }
    }
}

