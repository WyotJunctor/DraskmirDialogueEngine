namespace Graphmir.GraphObjects {
    
    public class EdgeMap<T, K> {

        public DefaultDictionary<T, HashSet<K>> labels = new DefaultDictionary<T, HashSet<K>>();

        public EdgeMap() {

        }

        public void Add(T labelKey, K labelValue) {
            labels[labelKey].Add(labelValue);
        }

        public void RemoveValue(T labelKey, K labelValue) {
            labels[labelKey].Remove(labelValue);
            if (labels[labelKey].Count == 0) {
                labels.Remove(labelKey);
            }
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
}