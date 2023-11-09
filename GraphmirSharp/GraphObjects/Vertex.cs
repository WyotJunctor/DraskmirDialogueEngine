namespace Graphmir.GraphObjects {

    public enum QueryTargetType { TgtVertex, RefVert, Edge, TgtLabel }
    public enum EdgeDirection { Ingoing, Outgoing, Undirected }

    public class LabelDelta {
        public HashSet<Label> addLabels = new HashSet<Label>();
        public HashSet<Label> delLabels = new HashSet<Label>();

        public LabelDelta(HashSet<Label> oldLabels, HashSet<Label> newLabels) {
            // which labels are new? labels that exist in newLabels but not in oldLabels
            // which labels are deleted? labels that exist in oldLabels but not in newLabels
            this.addLabels = new HashSet<Label>(newLabels.Except(oldLabels));
            this.delLabels = new HashSet<Label>(oldLabels.Except(newLabels));
        }
    }

    public class Vertex {
        public readonly Label vLabel;
        public uint lastUpdated;
        LocalIndex localIndex;

        HashSet<Label> labels = new HashSet<Label>();

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.lastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
            labels.Add(vLabel);
        }

        public Vertex(Label vLabel) : this(vLabel, Clock.globalTimestamp) {
        }

        public HashSet<T> QueryNeighborhood<T>(
            QueryTargetType queryTargetType,
            EdgeDirection dir = EdgeDirection.Outgoing,
            HashSet<Label>? refVertLabels = null, 
            HashSet<Label>? tgtVertLabels = null) 
        {
            // TODO
            return new HashSet<T>();
        }

        public void UpdateNeighborhood() {
            // TODO
            // if labels updated, tell invRefVerts?
        }

        public LabelDelta UpdateLabels() {
            // query neighborhood for 'is>' and update labels
            HashSet<Label> newLabels = QueryNeighborhood<Label>(
                QueryTargetType.TgtLabel, 
                dir:EdgeDirection.Outgoing,
                refVertLabels:new HashSet<Label>() {new Label("Is")});
            newLabels.Add(vLabel);
            LabelDelta labelDelta = new LabelDelta(labels, newLabels);
            labels = newLabels;
            PropagateLabels(labelDelta);
            return labelDelta;
        }

        public void PropagateLabels(LabelDelta labelDelta) {
            // pass labels to all neighbors and invRefVerts
            HashSet<Vertex> neighbors = new HashSet<Vertex>(localIndex.invRefVerts.Union(
                QueryNeighborhood<Vertex>(
                    QueryTargetType.TgtVertex,
                    dir:EdgeDirection.Undirected))
            );
            foreach (var neighbor in neighbors) {
                // todo neighbor.UpdateNeighborhood()
            }
        }

        public HashSet<Edge> GetEdges(EdgeDirection dir) {
            // get edges in direction
            return QueryNeighborhood<Edge>(QueryTargetType.Edge, dir:dir);
        }

        public HashSet<Vertex> GetInvRefVerts() {
            return localIndex.invRefVerts;
        }

        public HashSet<Vertex> GetDependents() {
            // get children via ingoing 'is' edges and invRefVerts
            return new HashSet<Vertex>(localIndex.invRefVerts.Union(
                QueryNeighborhood<Vertex>(
                    QueryTargetType.TgtVertex, 
                    dir:EdgeDirection.Ingoing,
                    refVertLabels:new HashSet<Label>() {new Label("Is")})));
        }

        public bool IsPrimaryRefVert() {
            return labels.Overlaps(EngineConfig.primaryTypes);
        }
    }
}