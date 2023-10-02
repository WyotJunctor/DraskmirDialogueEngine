namespace Graphmir.GraphObjects {
    public class Graph {

        struct RealizedMessage {
            public HashSet<Vertex> AddVerts, DelVerts;
            public HashSet<Edge> AddEdges, DelEdges;
        }

        public struct MessageResponse {
            public UpdateRecord updateRecord = new UpdateRecord();
            public Dictionary<Vertex, HashSet<Label>> labelAddMap = new Dictionary<Vertex, HashSet<Label>>();
            public Dictionary<Vertex, HashSet<Label>> labelDelMap = new Dictionary<Vertex, HashSet<Label>>();

            public MessageResponse() {}
        }

        public Dictionary<Label, Vertex> vertices = new Dictionary<Label, Vertex>();

        RealizedMessage Realize(GraphMessage message) {
            return new RealizedMessage();
        }

        public MessageResponse UpdateFrom(GraphMessage message) {
            RealizedMessage realizedMessage = Realize(message);
            MessageResponse response = new MessageResponse();

            var delPrimaryEdges = realizedMessage.DelEdges;

            // handle deleted vertices
                // add to deleted primary edges and secondary edges
            // foreach vertex
            //  remove from graph
            // all labels to lineage_del_map? 
            // tmpDelPrimaryEdges, tmpDelSecondaryEdges = clean up local index
            // add edges to respective lists

            // handle deleted primary edges
            //  src vert, if not deleted
            //      update local index with removed refVert, tgt tuples
            //          remove edge between tgtVert and refVert,
            //          if no edges remaining, remove refVert
            //  this results in some loss of labels
            //  propagate
            //  update realizedMessage.labelDelMap;

            // handle deleted secondary edges
            // we do this before added primary edges because 
            // it would be dumb to add labels and then immediately remove them
            // just remove the refVert, tgtVert edge in local index

            // handle added verts
            // just add it to the dictionary

            // handle added primary edges
            // 

            // handle added secondary edges

            // take changed labels and propagate to invRefVerts

            return response;
        }

    }
}