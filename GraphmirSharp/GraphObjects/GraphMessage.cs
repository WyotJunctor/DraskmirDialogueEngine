namespace Graphmir.GraphObjects {

    public enum EventType { Add, Delete, Duplicate, }

    public enum EventTarget { Vertex, Edge, }

    public class GraphMessage {
        public void MergeWith(GraphMessage other) {
            throw new NotImplementedException();
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