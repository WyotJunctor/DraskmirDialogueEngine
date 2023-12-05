namespace Graphmir.GameObjects {
    using Graphmir.GraphObjects;    

    public class Rule {

        protected Graph graph;
        protected Vertex vert;

        public Rule(Graph graph, Vertex vert) {
            this.graph = graph;
            this.vert = vert;
        }

        public virtual GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate) {
            return new GraphMessage();
        }

        public virtual Rule AddRule(Vertex vert) {
            return this;
        }
    }

    public class ReferenceRule : Rule {
        public ReferenceRule(Graph graph, Vertex vert) : base(graph, vert) {}
    }

    public class CopyRule : Rule {

        public CopyRule(Graph graph, Vertex vert) : base(graph, vert) {}

        public override Rule AddRule(Vertex vert)
        {
            return new CopyRule(graph, vert);
        }

        public override int GetHashCode()
        {
            return GetType().GetHashCode();
        }
    }

    public class RuleMap {
        public DefaultDictionary<Label, HashSet<Rule>> inherentRules = new DefaultDictionary<Label, HashSet<Rule>>();
        public DefaultDictionary<Label, HashSet<Rule>> inheritedRules = new DefaultDictionary<Label, HashSet<Rule>>();

        public GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate) {
            GraphMessage message = new GraphMessage();
            if (vert != null) {
                foreach (var rule in inheritedRules.TryGet(vert.vLabel)) {
                    message.MergeWith(rule.CheckRule(vert, edgeUpdate));
                }
            }
            return message;
        }

        public GraphMessage CheckRules(UpdateRecord updateRecord) {
            GraphMessage message = new GraphMessage();
            // iterate over rules of src, tgt, refVert, and invRefVert?
            // check rules and merge into graph message
            foreach (var edgeUpdate in updateRecord.edges) {
                message.MergeWith(CheckRule(edgeUpdate.src, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.tgt, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.refVert, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.invRefVert, edgeUpdate));
            }
            // return graph message
            return message;
        }

        public void DeleteRule(Vertex vert, Label label) {
            inheritedRules[vert.vLabel].ExceptWith(inherentRules[label]);
        }

        public void AddRule(Vertex vert, Label label) {
            foreach (var rule in inherentRules[label]) {
                inheritedRules[vert.vLabel].Add(rule.AddRule(vert));
            }
        }
    }

    public delegate Rule RuleFactory(Graph graph, Vertex vert);
}