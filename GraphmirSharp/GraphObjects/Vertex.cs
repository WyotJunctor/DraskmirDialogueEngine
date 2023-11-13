namespace Graphmir.GraphObjects {

    public enum QueryTargetType { TgtVertex, RefVert, Edge, TgtLabel }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }

    public class LabelDelta {
        public LabelSet addLabels = new LabelSet();
        public LabelSet delLabels = new LabelSet();

        public LabelDelta(
            LabelSet oldLabels,
            LabelSet newLabels) {
            // which labels are new? labels that exist in newLabels but not in oldLabels
            // which labels are deleted? labels that exist in oldLabels but not in newLabels
            
            this.addLabels = newLabels.Except(oldLabels); // SetDifference(newLabels, oldLabels);
            this.delLabels = oldLabels.Except(newLabels); // SetDifference(oldLabels, newLabels); 
        }


        // TODO: put this code in the labelSet definition
        public Dictionary<Label, HashSet<Label>> SetDifference(
            DefaultDictionary<Label, HashSet<Label>> srcLabels,
            DefaultDictionary<Label, HashSet<Label>> tgtLabels) 
        {
            Dictionary<Label, HashSet<Label>> labelDiff = new Dictionary<Label, HashSet<Label>>();
            
            foreach (var keyPair in srcLabels) {
                HashSet<Label> labels = new HashSet<Label>(tgtLabels.TryGet(keyPair.Key).Except(keyPair.Value));
                if (labels.Count > 0) {
                    labelDiff[keyPair.Key] = labels;
                }
            }

            return labelDiff;
        }
    }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex localIndex;

        LabelSet labels = new LabelSet();

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
            labels.Add(vLabel);
        }

        public Vertex(Label vLabel) : this(vLabel, Clock.globalTimestamp) {
        }

        public T QueryNeighborhood<T> (
            QueryTargetType queryTargetType,
            EdgeDirection dir = EdgeDirection.Outgoing,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null) where T : new()
        {
            // TODO
            return new T();
        }

        public void UpdateNeighborhood() {
            // TODO
            // if labels updated, tell invRefVerts?
        }

        public LabelDelta UpdateLabels() {
            // query neighborhood for 'is>' and update labels
            LabelSet newLabels = QueryNeighborhood<LabelSet>(
                QueryTargetType.TgtLabel, 
                dir:EdgeDirection.Outgoing,
                refVertLabels:EngineConfig.primaryTypes);
            newLabels.Add(vLabel);
            LabelDelta labelDelta = new LabelDelta(labels, newLabels);
            labels = newLabels;
            PropagateLabels(labelDelta);
            return labelDelta;
        }

        public void PropagateLabels(LabelDelta labelDelta) {
            // pass labels to all neighbors and invRefVerts
            HashSet<Vertex> neighbors = new HashSet<Vertex>(localIndex.invRefVerts.Union(
                QueryNeighborhood<HashSet<Vertex>>(
                    QueryTargetType.TgtVertex,
                    dir:EdgeDirection.Undirected))
            );
            foreach (var neighbor in neighbors) {
                // todo neighbor.UpdateNeighborhood()
            }
        }

        public HashSet<Edge> GetEdges(EdgeDirection dir) {
            // get edges in direction
            return QueryNeighborhood<HashSet<Edge>>(QueryTargetType.Edge, dir:dir);
        }

        public HashSet<Vertex> GetInvRefVerts() {
            return localIndex.invRefVerts;
        }

        public HashSet<Vertex> GetDependents() {
            // get children via ingoing 'is' edges and invRefVerts
            return new HashSet<Vertex>(localIndex.invRefVerts.Union(
                QueryNeighborhood<HashSet<Vertex>>(
                    QueryTargetType.TgtVertex, 
                    dir:EdgeDirection.Ingoing,
                    refVertLabels:EngineConfig.primaryTypes)));
        }

        public bool IsPrimaryRefVert() {
            return labels.Overlaps(EngineConfig.primaryLabel, EngineConfig.primaryTypes);
        }
    }
}