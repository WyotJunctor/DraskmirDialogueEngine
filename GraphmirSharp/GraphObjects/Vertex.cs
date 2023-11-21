namespace Graphmir.GraphObjects {

    public enum QueryTargetType { TgtVert, RefVert, Edge, TgtLabel }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }
    public enum GraphOp { Add, Remove };

    public class LabelDelta {
        public EdgeMap<Label, Label> addLabels = new EdgeMap<Label, Label>();
        public EdgeMap<Label, Label> delLabels = new EdgeMap<Label, Label>();

        public LabelDelta(
            EdgeMap<Label, Label> oldLabels,
            EdgeMap<Label, Label> newLabels) {
            // which labels are new? labels that exist in newLabels but not in oldLabels
            // which labels are deleted? labels that exist in oldLabels but not in newLabels
            
            this.addLabels = newLabels.Except(oldLabels); // SetDifference(newLabels, oldLabels);
            this.delLabels = oldLabels.Except(newLabels); // SetDifference(oldLabels, newLabels); 
        }
    }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex outgoingLocalIndex, ingoingLocalIndex;
        public HashSet<Vertex> invRefVerts = new HashSet<Vertex>();

        EdgeMap<Label, Label> labels = new EdgeMap<Label, Label>();

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.outgoingLocalIndex = new LocalIndex(); 
            this.ingoingLocalIndex = new LocalIndex();
            labels.Add(vLabel, EngineConfig.primaryLabel);
        }

        public Vertex(Label vLabel) : this(vLabel, Clock.globalTimestamp) {
        }

        /*
    HashSet<Vertex/Edge/Label>
    public enum QueryTargetType { TgtVertex, RefVert, Edge, TgtLabel }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }
        */
        public HashSet<Vertex> QueryNeighborhoodVertex (
            QueryTargetType queryTargetType,
            EdgeDirection dir,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null)
        {
            if (dir == EdgeDirection.Undirected) {
                return new HashSet<Vertex>(QueryNeighborhoodVertex(
                    queryTargetType, EdgeDirection.Ingoing, refVertLabels, tgtVertLabels).Union(
                        QueryNeighborhoodVertex(
                            queryTargetType, EdgeDirection.Outgoing, refVertLabels, tgtVertLabels)
                        )
                    );
            }
            LocalIndex targetIndex = (dir == EdgeDirection.Ingoing) ? ingoingLocalIndex : outgoingLocalIndex;
            QueryTargetType srcType = queryTargetType;
            QueryTargetType dstType = (queryTargetType == QueryTargetType.RefVert) ? QueryTargetType.TgtVert : QueryTargetType.RefVert;  
            HashSet<Label>? srcLabels = (queryTargetType == QueryTargetType.RefVert) ? refVertLabels: tgtVertLabels;
            HashSet<Label>? dstLabels = (queryTargetType == QueryTargetType.RefVert) ? tgtVertLabels: refVertLabels; 

            HashSet<Vertex> srcVerts = new HashSet<Vertex>();
            if (srcLabels != null) {
                srcVerts.UnionWith(targetIndex.GetVertsFromLabels(srcType, srcLabels, EngineConfig.primaryLabel));
            }
            else {
                srcVerts = new HashSet<Vertex>((queryTargetType == QueryTargetType.RefVert) ? targetIndex.refVertToLabel.Keys : targetIndex.tgtVertToLabel.Keys);
            }
            if (dstLabels != null) {
                HashSet<Vertex> dstVerts = targetIndex.GetVertsFromLabels(dstType, dstLabels, EngineConfig.primaryLabel);
                srcVerts.IntersectWith(targetIndex.GetVertsFromVerts(srcType, dstVerts));
            }
            return srcVerts;
        }

        // add/remove edge
        // add/remove refVert
        // add/remove edge between tgtVert/refVert and refVert/label
        // when you add a vert, remember to link its labels
        public void UpdateNeighborhood<T>(GraphOp graphOp, QueryTargetType targetType, T target) {
            // TODO
            // if labels updated, tell invRefVerts?
        }

        public LabelDelta UpdateLabels() {
            EdgeMap<Label, Label> newLabels = new EdgeMap<Label, Label>();
            // iterate over primary edges and get labels
            foreach (var edgeLabel in EngineConfig.primaryTypes) {
                if (outgoingLocalIndex.labelToRefVert.ContainsKey(edgeLabel)) {
                    // foreach ref vert in labelToRefVert ("Is"), so the refVert 'is' an Is or Was
                    foreach (var refVert in outgoingLocalIndex.labelToRefVert[edgeLabel].labels.TryGet(EngineConfig.primaryLabel)) {
                        // foreach tgt vert in refVertToTgtVert
                        foreach (var tgtVert in outgoingLocalIndex.refVertToTgtVert[refVert]) {
                            // foreach primary edge label
                            foreach (var tgtEdgeLabel in EngineConfig.primaryTypes) {
                                // foreach label, HashSet<Label> in tgtVertToLabel (primaryTypes), overwrite label 
                                foreach (var tgtLabel in outgoingLocalIndex.tgtVertToLabel[tgtVert].labels.TryGet(tgtEdgeLabel)) {
                                    if (EngineConfig.labelPriority[edgeLabel] > EngineConfig.labelPriority[tgtEdgeLabel]) {
                                        newLabels.Add(edgeLabel, tgtLabel);
                                    }
                                    else {
                                        newLabels.Add(tgtEdgeLabel, tgtLabel);
                                    }
                                }
                            }
                        }
                    }     
                }
            }
            newLabels.Add(EngineConfig.primaryLabel, vLabel);
            LabelDelta labelDelta = new LabelDelta(labels, newLabels);
            labels = newLabels;
            PropagateLabels(labelDelta);
            return labelDelta;
        }

        public void PropagateLabels(LabelDelta labelDelta) {
            // pass labels to all neighbors and invRefVerts
            HashSet<Vertex> neighbors = new HashSet<Vertex>(invRefVerts.Union(
                QueryNeighborhoodVertex(
                    QueryTargetType.TgtVert,
                    dir:EdgeDirection.Undirected))
            );
            foreach (var neighbor in neighbors) {
                // todo neighbor.UpdateNeighborhood(add all your labels)
            }
        }

        /*
        public Edge(Vertex src, Vertex tgt, Vertex refVert) {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }
        refVertToTgtVert = new Dictionary<Vertex, HashSet<Vertex>>(),
        */
        public HashSet<Edge> GetEdges(EdgeDirection dir) {
            // get edges in direction 
            HashSet<Edge> edges = new HashSet<Edge>();
            if (dir == EdgeDirection.Undirected) {
                edges = new HashSet<Edge>(GetEdges(EdgeDirection.Ingoing).Union(GetEdges(EdgeDirection.Outgoing)));
            }
            var targetIndex = (dir == EdgeDirection.Ingoing) ? ingoingLocalIndex: outgoingLocalIndex;
            foreach (var keyPair in targetIndex.refVertToTgtVert) {
                foreach (var tgtVert in keyPair.Value) {
                    edges.Add(new Edge(this, tgtVert, keyPair.Key));
                }
            }
            return edges;
        }

        public HashSet<Vertex> GetInvRefVerts() {
            return invRefVerts;
        }

        public HashSet<Vertex> GetDependents() {
            // get children via ingoing 'is' edges and invRefVerts
            return new HashSet<Vertex>(invRefVerts.Union(
                QueryNeighborhoodVertex(
                    QueryTargetType.TgtVert, 
                    dir:EdgeDirection.Ingoing,
                    refVertLabels:EngineConfig.primaryTypes)));
        }

        public bool IsPrimaryRefVert() {
            return labels.Overlaps(EngineConfig.primaryLabel, EngineConfig.primaryTypes);
        }
    }
}