namespace Graphmir.GraphObjects {

    public enum EventType { Add, Delete, Duplicate, }

    public enum EventTarget { Vertex, Edge, }


    public class LabelSet {

        DefaultDictionary<Label, HashSet<Label>> labels = new DefaultDictionary<Label, HashSet<Label>>();

        public LabelSet() {

        }

        public void Add(Label labelKey, Label labelValue) {
            labels[labelKey].Add(labelValue);
        }

        public void Add(Label labelValue) {
            labels[EngineConfig.primaryLabel].Add(labelValue);
        } 

        public void UnionWith(LabelSet labelSet) {
            // iterate over keys and union hashsets of labels
            foreach (var keyPair in labelSet.labels) {
                this.labels[keyPair.Key].UnionWith(keyPair.Value);
            }
        }

        public bool Overlaps(Label labelKey, HashSet<Label> tgtLabels) {
            return labels.TryGet(labelKey).Overlaps(tgtLabels);
        }

        public LabelSet Except(LabelSet labelSet) {
            LabelSet labelDiff = new LabelSet();
            foreach (var keyPair in this.labels) {
                HashSet<Label> labels = new HashSet<Label>(keyPair.Value.Except(labelSet.labels.TryGet(keyPair.Key)));
                if (labels.Count > 0) {
                    labelDiff.labels[keyPair.Key] = labels;
                }
            }
            return labelDiff;
        }

        public void ExceptWith(LabelSet labelSet) {
            List<Label> labelsToRemove = new List<Label>();
            foreach (var keyPair in labels) {
                keyPair.Value.ExceptWith(labelSet.labels.TryGet(keyPair.Key));
                if (keyPair.Value.Count == 0) {
                    labelsToRemove.Add(keyPair.Key);
                }
            }
            foreach (var key in labelsToRemove) {
                labels.Remove(key);
            }
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

    public class GraphMessage {
        public HashSet<Label> addVerts = new HashSet<Label>();
        public HashSet<Label> delVerts = new HashSet<Label>();
        public HashSet<EdgeContainer> addEdges = new HashSet<EdgeContainer>();
        public HashSet<EdgeContainer> delEdges = new HashSet<EdgeContainer>();

        public void MergeWith(GraphMessage other) {
            // currently, we are allowing vertices to exist in both del verts and add verts
            // this is because the deletion might be important independent of the vertex's re-creation
            addVerts.UnionWith(other.addVerts);
            delVerts.UnionWith(other.delVerts);
            addEdges.UnionWith(other.addEdges);
            delEdges.UnionWith(other.delEdges);
        }
    }

    public class UpdateRecord {
        HashSet<Edge> addEdges = new HashSet<Edge>(), delEdges = new HashSet<Edge>();

        public void AddEdge(Edge edge, bool add) {
            if (add == true) {
                addEdges.Add(edge);
                delEdges.Remove(edge);
            }
            else {
                delEdges.Add(edge);
                addEdges.Remove(edge);
            }
        }

        public bool IsEmpty() {
            return addEdges.Count == 0 && delEdges.Count == 0;
        }

        public void MergeWith(UpdateRecord record) {
            addEdges.UnionWith(record.addEdges);
            delEdges.ExceptWith(record.addEdges);
            delEdges.UnionWith(record.delEdges);
            addEdges.ExceptWith(record.delEdges);
        }
    }
}