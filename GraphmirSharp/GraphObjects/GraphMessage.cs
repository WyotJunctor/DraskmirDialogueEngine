namespace Graphmir.GraphObjects {

    public enum EventType { Add, Delete, Duplicate, }

    public enum EventTarget { Vertex, Edge, }


    public class EdgeMap<T, K> {

        public DefaultDictionary<T, HashSet<K>> labels = new DefaultDictionary<T, HashSet<K>>();

        public EdgeMap() {

        }

        public void Add(T labelKey, K labelValue) {
            labels[labelKey].Add(labelValue);
        }

        /*
        public void Add(T labelValue) {
            labels[EngineConfig.primaryLabel].Add(labelValue);
        } 
        */

        public void UnionWith(EdgeMap<T, K> labelSet) {
            // iterate over keys and union hashsets of labels
            foreach (var keyPair in labelSet.labels) {
                this.labels[keyPair.Key].UnionWith(keyPair.Value);
            }
        }

        public bool Overlaps(T labelKey, HashSet<K> tgtLabels) {
            return labels.TryGet(labelKey).Overlaps(tgtLabels);
        }

        public EdgeMap<T, K> Except(EdgeMap<T, K> labelSet) {
            EdgeMap<T, K> labelDiff = new EdgeMap<T, K>();
            foreach (var keyPair in this.labels) {
                HashSet<K> labels = new HashSet<K>(keyPair.Value.Except(labelSet.labels.TryGet(keyPair.Key)));
                if (labels.Count > 0) {
                    labelDiff.labels[keyPair.Key] = labels;
                }
            }
            return labelDiff;
        }

        public void ExceptWith(EdgeMap<T, K> labelSet) {
            List<T> labelsToRemove = new List<T>();
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