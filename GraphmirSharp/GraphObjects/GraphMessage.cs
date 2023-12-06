namespace Graphmir.GraphObjects {

    public class GraphMessage {
        public HashSet<Label> addVerts = new HashSet<Label>();
        public HashSet<Label> delVerts = new HashSet<Label>();
        public HashSet<Edge<Label>> addEdges = new HashSet<Edge<Label>>();
        public HashSet<Edge<Label>> delEdges = new HashSet<Edge<Label>>();

        public bool MergeWith(GraphMessage other) {
            // currently, we are allowing vertices to exist in both del verts and add verts
            // this is because the deletion might be important independent of the vertex's re-creation
            bool updated = false;
            updated = updated || !other.addVerts.IsSubsetOf(addVerts);
            addVerts.UnionWith(other.addVerts);
            updated = updated || !other.delVerts.IsSubsetOf(delVerts);
            delVerts.UnionWith(other.delVerts);
            updated = updated || !other.addEdges.IsSubsetOf(addEdges);
            addEdges.UnionWith(other.addEdges);
            updated = updated || !other.delEdges.IsSubsetOf(delEdges);
            delEdges.UnionWith(other.delEdges);
            return updated;
        }

        public GraphMessage Copy() {
            GraphMessage message = new GraphMessage();
            message.addVerts = new HashSet<Label>(message.addVerts);
            message.delVerts = new HashSet<Label>(message.delVerts);
            message.addEdges = new HashSet<Edge<Label>>(message.addEdges);
            message.delEdges = new HashSet<Edge<Label>>(message.delEdges);
            return message;
        }
    }

    public class JSONEdge {
        public string src {get; set;}
        public string tgt {get; set;}
        public string refVert {get; set;}
    }

    // this class exists for deserialization purposes
    public class JSONGraphMessage {
        
        public List<string> verts {get; set;}
        public List<JSONEdge> edges {get; set;}

        public GraphMessage ToGraphMessage() 
        {
            GraphMessage message = new GraphMessage();
            foreach (var label in verts) {
                message.addVerts.Add(new Label(label));
            }    
            foreach (var edge in edges) {
                message.addEdges.Add(new Edge<Label>(new Label(edge.src), new Label(edge.tgt), new Label(edge.refVert)));
            }
            return message;
        }

    }
}