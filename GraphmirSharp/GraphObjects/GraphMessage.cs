namespace Graphmir.GraphObjects {

    public enum EventType { Add, Delete, Duplicate, }

    public enum EventTarget { Vertex, Edge, }

    public class GraphMessage {
        public void UpdateFrom(GraphMessage other) {
            throw new NotImplementedException();
        }
    }

    public class UpdateRecord {

    }
}