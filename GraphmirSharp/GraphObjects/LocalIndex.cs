namespace Graphmir.GraphObjects {
    public class LocalIndex {

        public DefaultDictionary<Vertex, EdgeMap<Label, Label>> 
            refVertToLabel = new DefaultDictionary<Vertex, EdgeMap<Label, Label>>(), 
            tgtVertToLabel = new DefaultDictionary<Vertex, EdgeMap<Label, Label>>();
        public DefaultDictionary<Label, EdgeMap<Label, Vertex>> 
            labelToRefVert = new DefaultDictionary<Label, EdgeMap<Label, Vertex>>(),
            labelToTgtVert = new DefaultDictionary<Label, EdgeMap<Label, Vertex>>();
        public DefaultDictionary<Vertex, HashSet<Vertex>> 
            refVertToTgtVert = new DefaultDictionary<Vertex, HashSet<Vertex>>(), 
            tgtVertToRefVert = new DefaultDictionary<Vertex, HashSet<Vertex>>();

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

        public void AddTgtVertToRefVert(Vertex tgtVert, Vertex refVert) {
            tgtVertToRefVert[tgtVert].Add(refVert);
            if (tgtVertToLabel.ContainsKey(tgtVert) == false) {
                tgtVertToLabel[tgtVert] = new EdgeMap<Label, Label>();
            }
            refVertToTgtVert[refVert].Add(tgtVert);
            if (refVertToLabel.ContainsKey(refVert) == false) {
                refVertToLabel[refVert] = new EdgeMap<Label, Label>();
            }
        }

        /*
        public Dictionary<Vertex, EdgeMap<Label, Label>> 
            refVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>(), 
            tgtVertToLabel = new Dictionary<Vertex, EdgeMap<Label, Label>>();
        public Dictionary<Label, EdgeMap<Label, Vertex>> 
            labelToRefVert = new Dictionary<Label, EdgeMap<Label, Vertex>>(),
            labelToTgtVert = new Dictionary<Label, EdgeMap<Label, Vertex>>();
        */
        public void UpdateVertLabels(QueryTargetType queryTargetType, Vertex vert, LabelDelta labelDelta) {//EdgeMap<Label, Label> labels) {
            // if refVert, then pick relevant label maps
            if (queryTargetType == QueryTargetType.RefVert && refVertToLabel.ContainsKey(vert) == false) {
                return;
            }
            var vertToLabelMap = (queryTargetType == QueryTargetType.TgtVert) ? tgtVertToLabel : refVertToLabel;
            var labelToVertMap = (queryTargetType == QueryTargetType.TgtVert) ? labelToTgtVert : labelToRefVert;
           // var edgesToAdd = labels.Except(vertToLabelMap.TryGet(vert));
            // add labels not already there
            foreach (var keyPair in labelDelta.addLabels.labels) {
                Label edgeLabel = keyPair.Key;
                foreach (var label in keyPair.Value) {
                    vertToLabelMap[vert].Add(edgeLabel, label);
                    labelToVertMap[label].Add(edgeLabel, vert);
                }
            }
            // get which labels to remove from the vert
            if (vertToLabelMap.ContainsKey(vert)) {
                foreach (var keyPair in labelDelta.delLabels.labels) {
                    Label edgeLabel = keyPair.Key;
                    foreach (var label in keyPair.Value) {
                        vertToLabelMap[vert].RemoveValue(edgeLabel, label);
                        labelToVertMap[label].RemoveValue(edgeLabel, vert);
                        // check to remove
                        // if label has no more edges, remove
                        if (labelToVertMap[label].labels.Count == 0) {
                            labelToVertMap.Remove(label);
                        }
                        // if vert has no more labels, remove? 
                        // I think we can ignore this for now since a vertex will never end up with zero labels as a result of this method
                    }
                }
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