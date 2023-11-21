namespace Graphmir.GraphObjects {
    public class LocalIndex {

        public Dictionary<Vertex, EdgeMap<Label, Label>> 
            refVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>(), 
            tgtVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>();
        public Dictionary<Label, EdgeMap<Label, Vertex>> 
            labelToRefVert = new Dictionary<Label, EdgeMap<Label, Vertex>>(),
            labelToTgtVert = new Dictionary<Label, EdgeMap<Label, Vertex>>();
        public Dictionary<Vertex, HashSet<Vertex>> 
            refVertToTgtVert = new Dictionary<Vertex, HashSet<Vertex>>(), 
            tgtVertToRefVert = new Dictionary<Vertex, HashSet<Vertex>>();

        void DeleteVertFromLabelMap(
            Vertex vert, 
            Dictionary<Vertex, EdgeMap<Label, Label>> vertTolabelMap, 
            Dictionary<Label, EdgeMap<Label, Vertex>> labelToVertMap) 
        {
            foreach (var keyPair in vertTolabelMap[vert].labels) {
                // label, hashSet
                foreach (var label in keyPair.Value) {
                    labelToVertMap[label].RemoveValue(label, vert);
                    if (labelToRefVert[label].labels.Count == 0 && labelToTgtVert[label].labels.Count == 0) {
                        labelToRefVert.Remove(label);
                        labelToTgtVert.Remove(label);
                    }
                }
            }
            vertTolabelMap.Remove(vert);
        }

        public void DeleteRefVert(Vertex refVert) {
            // remove from refVert to label
            if (!refVertToLabel.ContainsKey(refVert)) {
                return;
            }

            // foreach label
            foreach (var tgtVert in refVertToTgtVert[refVert]) {
                tgtVertToRefVert[tgtVert].Remove(refVert);
                if (tgtVertToRefVert[tgtVert].Count == 0) {
                    // delete this tgtVert, but now you need to check labels
                    tgtVertToRefVert.Remove(tgtVert);
                    DeleteVertFromLabelMap(tgtVert, tgtVertToLabel, labelToTgtVert);
                }
            }
            refVertToTgtVert.Remove(refVert);
            DeleteVertFromLabelMap(refVert, refVertToLabel, labelToRefVert);
        } 

        public bool DeleteVertConnection(Vertex srcVert, Vertex dstVert, Dictionary<Vertex, HashSet<Vertex>> vertMap) {
            vertMap[srcVert].Remove(dstVert);
            if (vertMap[srcVert].Count == 0) {
                vertMap.Remove(dstVert);
                return true;
            }
            return false;
        }

        public void DeleteTgtVertToRefVert(Vertex tgtVert, Vertex refVert) {
            // remove refVert from tgtVert
            if (DeleteVertConnection(refVert, tgtVert, refVertToTgtVert)) {
                DeleteVertFromLabelMap(refVert, refVertToLabel, labelToRefVert);
            }
            if (DeleteVertConnection(tgtVert, refVert, tgtVertToRefVert)) {
                DeleteVertFromLabelMap(tgtVert, tgtVertToLabel, labelToTgtVert);
            }
        }

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