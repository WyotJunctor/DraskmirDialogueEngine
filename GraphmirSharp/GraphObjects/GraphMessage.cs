namespace Graphmir.GraphObjects {

    public class GraphMessage {
        public HashSet<Label> addVerts = new HashSet<Label>();
        public HashSet<Label> delVerts = new HashSet<Label>();
        public HashSet<EdgeContainer> addEdges = new HashSet<EdgeContainer>();
        public HashSet<EdgeContainer> delEdges = new HashSet<EdgeContainer>();

        public bool MergeWith(GraphMessage other) {
            // currently, we are allowing vertices to exist in both del verts and add verts
            // this is because the deletion might be important independent of the vertex's re-creation
            bool isSubset = false;
            isSubset = isSubset || other.addVerts.IsSubsetOf(addVerts);
            addVerts.UnionWith(other.addVerts);
            isSubset = isSubset || other.delVerts.IsSubsetOf(delVerts);
            delVerts.UnionWith(other.delVerts);
            isSubset = isSubset || other.addEdges.IsSubsetOf(addEdges);
            addEdges.UnionWith(other.addEdges);
            isSubset = isSubset || other.delEdges.IsSubsetOf(delEdges);
            delEdges.UnionWith(other.delEdges);
            return isSubset;
        }

        public GraphMessage Copy() {
            GraphMessage message = new GraphMessage();
            message.addVerts = new HashSet<Label>(message.addVerts);
            message.delVerts = new HashSet<Label>(message.delVerts);
            message.addEdges = new HashSet<EdgeContainer>(message.addEdges);
            message.delEdges = new HashSet<EdgeContainer>(message.delEdges);
            return message;
        }
    }
}