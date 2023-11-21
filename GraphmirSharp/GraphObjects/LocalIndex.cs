namespace Graphmir.GraphObjects {
    public class LocalIndex {

        public HashSet<Label> labels = new HashSet<Label>();

        public Dictionary<Vertex, EdgeMap<Label, Label>> 
            refVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>(), 
            tgtVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>();
        public Dictionary<Label, EdgeMap<Label, Vertex>> 
            labelToRefVert = new Dictionary<Label, EdgeMap<Label, Vertex>>(),
            labelToTgtVert = new Dictionary<Label, EdgeMap<Label, Vertex>>();
        public Dictionary<Vertex, HashSet<Vertex>> 
            refVertToTgtVert = new Dictionary<Vertex, HashSet<Vertex>>(), 
            tgtVertToRefVert = new Dictionary<Vertex, HashSet<Vertex>>();

        public HashSet<Vertex> GetVertsFromLabels(QueryTargetType queryTargetType, HashSet<Label> labels, params Label[] edgeLabels) {
            HashSet<Vertex> verts = new HashSet<Vertex>();
            foreach (var label in labels) {
                verts.UnionWith(GetVertsFromLabel(queryTargetType, label, edgeLabels));
            }
            return verts;
        }

        public HashSet<Vertex> GetVertsFromLabel(QueryTargetType queryTargetType, Label label, params Label[] edgeLabels) {
            HashSet<Vertex> verts = new HashSet<Vertex>();
            Dictionary<Label, EdgeMap<Label, Vertex>> edgeMap = (queryTargetType == QueryTargetType.TgtVert) ? labelToTgtVert : labelToRefVert;
            if (edgeMap.ContainsKey(label)) {
                foreach (var edgeLabel in edgeLabels) {
                    if (edgeMap[label].labels.ContainsKey(edgeLabel)) {
                        verts.UnionWith(edgeMap[label].labels[edgeLabel]);
                    }
                }
            }
            return verts;
        }

        public HashSet<Vertex> GetVertsFromVerts(QueryTargetType queryTargetType, HashSet<Vertex> verts) {
            HashSet<Vertex> returnVerts = new HashSet<Vertex>();
            var targetMap = (queryTargetType == QueryTargetType.TgtVert) ? refVertToTgtVert: tgtVertToRefVert;
            foreach (var vert in verts) {
                if (targetMap.ContainsKey(vert)) {
                    returnVerts.UnionWith(targetMap[vert]);
                }
            }
            return returnVerts;
        }
    }
}