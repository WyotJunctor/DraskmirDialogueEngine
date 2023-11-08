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

            // iteratively
            //    apply effect rules
            //    end if no more changes produced by effect
            //    apply deconflict rules

            // build a new graph message of the final,
            // deconflicted effect deltas
            // return that

            throw new NotImplementedException();
        }
    }
}