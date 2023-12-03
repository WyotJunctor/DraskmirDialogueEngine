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
        // invRefVert.UpdateNeighborhood(delete vert from refVerts);
        // edge.src.UpdateNeighborhood(delete (edge.refVert, edge.tgt) from local index);
        // edge.src.UpdateNeighborhood(add (refVert, edge.tgt) to local index);
        // neighbor.UpdateNeighborhood(add your edge map/labels)


        public void DeleteRefVert(Vertex refVert) {
            ingoingLocalIndex.DeleteRefVert(refVert);
            outgoingLocalIndex.DeleteRefVert(refVert);
        }

        public void DeleteEdge(Edge edge, EdgeDirection dir) {
            var targetIndex = (dir == EdgeDirection.Ingoing) ? ingoingLocalIndex: outgoingLocalIndex;
            Vertex otherVert = (dir == EdgeDirection.Ingoing) ? edge.src : edge.tgt;
            // remove otherVert - refVert relationship from graph
            targetIndex.DeleteTgtVertToRefVert(otherVert, edge.refVert);
        }

        public void AddEdge(Edge edge, EdgeDirection dir) {
            // get index and otherVert
            var targetIndex = (dir == EdgeDirection.Ingoing) ? ingoingLocalIndex: outgoingLocalIndex;
            Vertex otherVert = (dir == EdgeDirection.Ingoing) ? edge.src : edge.tgt;
            // add each other to appropriate vertMap
            edge.refVert.invRefVerts.Add(this);
            targetIndex.AddTgtVertToRefVert(otherVert, edge.refVert);
        }

        public LabelDelta UpdateLabels() {
            EdgeMap<Label, Label> newLabels = new EdgeMap<Label, Label>();
            // iterate over primary edges and get labels
            foreach (var edgeLabel in EngineConfig.primaryTypes) {
                if (outgoingLocalIndex.labelToRefVert.ContainsKey(edgeLabel)) {
                    // foreach ref vert in labelToRefVert ("Is"), so the refVert 'is' an Is or Was
                    foreach (var refVert in outgoingLocalIndex.labelToRefVert[edgeLabel].labels.TryGet(EngineConfig.primaryLabel)) {
                        // foreach tgt vert in refVertToTgtVert
                        foreach (var tgtVert in outgoingLocalIndex.refVertToTgtVert.TryGet(refVert)) {
                            // foreach primary edge label
                            foreach (var tgtEdgeLabel in EngineConfig.primaryTypes) {
                                // foreach label, HashSet<Label> in tgtVertToLabel (primaryTypes), overwrite label
                                foreach (var tgtLabel in outgoingLocalIndex.tgtVertToLabel.TryGet(tgtVert).labels.TryGet(tgtEdgeLabel)) {
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

        public void UpdateNeighborLabels(Vertex neighbor, LabelDelta labelDelta, QueryTargetType queryTargetType, EdgeDirection dir) {
            if (queryTargetType == QueryTargetType.RefVert && dir == EdgeDirection.Undirected) {
                UpdateNeighborLabels(neighbor, labelDelta, queryTargetType, EdgeDirection.Ingoing);
                dir = EdgeDirection.Outgoing;
            }
            var targetIndex = (dir == EdgeDirection.Ingoing) ? ingoingLocalIndex : outgoingLocalIndex;
            targetIndex.UpdateVertLabels(queryTargetType, neighbor, labelDelta);
        }

        public void PropagateLabels(LabelDelta labelDelta) {
            // pass labels to all neighbors and invRefVerts
            HashSet<Vertex> ingoingNeighbors =  QueryNeighborhoodVertex(QueryTargetType.TgtVert, EdgeDirection.Ingoing);
            HashSet<Vertex> outgoingNeighbors = QueryNeighborhoodVertex(QueryTargetType.TgtVert, EdgeDirection.Outgoing);
            foreach (var neighbor in ingoingNeighbors) {
                neighbor.UpdateNeighborLabels(this, labelDelta, QueryTargetType.TgtVert, EdgeDirection.Ingoing);
            }
            foreach (var neighbor in outgoingNeighbors) {
                neighbor.UpdateNeighborLabels(this, labelDelta, QueryTargetType.TgtVert, EdgeDirection.Outgoing);
            }
            foreach (var neighbor in invRefVerts) {
                neighbor.UpdateNeighborLabels(this, labelDelta, QueryTargetType.RefVert, EdgeDirection.Undirected);
            }
        }

        /*
        public Edge(Vertex src, Vertex tgt, Vertex refVert) {
            this.src = src;
            this.tgt = tgt;
            this.refVert = refVert;
        }
        refVertToTgtVert = new DefaultDictionary<Vertex, HashSet<Vertex>>(),
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