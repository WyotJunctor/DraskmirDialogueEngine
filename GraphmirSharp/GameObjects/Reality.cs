namespace Graphmir {
    using GraphObjects;

    public class Clock {
        public static uint globalTimestamp;
    }

    public class Reality {

        Graph graph;

        public Reality(Graph graph) {
            this.graph = graph;
        }

        public GraphMessage ReceiveMessage(GraphMessage message) {

            // instantiate full message

            // iteratively
            // instantiate UpdateRecords
            // merge GraphMessage into full message
            // process GraphMessage and produce MessageResponse
            // use MessageResponse.labelAddMap and labelDelMap to handle rule propagation
            // use MessageResponse to update UpdateRecords
            // use DeconflictRules on updated verts to generate GraphMessage
            // merge GraphMessage into full message
            // process GraphMessage and produce MessageResponse
            // use MessageResponse.labelAddMap and labelDelMap to handle rule propagation
            // use MessageResponse to update UpdateRecords
            // use EffectRules on updated verts to generate GraphMessage... loop back

            // return full message

            throw new NotImplementedException();
        }
    }
}