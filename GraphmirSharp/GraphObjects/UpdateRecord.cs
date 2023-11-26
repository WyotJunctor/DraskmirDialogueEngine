namespace Graphmir.GraphObjects {
        public class UpdateRecord {
        HashSet<EdgeUpdate> edges = new HashSet<EdgeUpdate>();

        public void AddEdge(EdgeUpdate edge) {
            edges.Add(edge);
        }

        public bool IsEmpty() {
            return edges.Count == 0;
        }

        public void MergeWith(UpdateRecord record) {
            edges.Union(record.edges);
        }
    }
}