namespace Graphmir {
    using GraphObjects;

    public class Clock {
        public static uint globalTimestamp;
    }

    public class Rule {
        // TODO
    }

    public class VertexRuleContainer {
        public HashSet<Rule> inherentRules = new HashSet<Rule>(), inheritedRules = new HashSet<Rule>();
    }

    public class RuleMap {
        public DefaultDictionary<Label, VertexRuleContainer> vertexRules = new DefaultDictionary<Label, VertexRuleContainer>();
    }

    public class Reality {

        Graph graph;
        // structure which maps vertices to rules
        RuleMap deconflictRules = new RuleMap();
        RuleMap effectRules = new RuleMap();

        public Reality(Graph graph) {
            this.graph = graph;
        }

        GraphMessage ProcessRules(UpdateRecord updateRecord, RuleMap ruleMap) {
            // TODO
            return new GraphMessage();
        }

        void PropagateRules(MessageResponse reponse) {
            // TODO
        }

        UpdateRecord UpdateGraph(GraphMessage message) {
            // process GraphMessage and produce MessageResponse
            MessageResponse response = graph.UpdateFrom(message);
            // use MessageResponse.labelAddMap and labelDelMap to handle rule propagation
            PropagateRules(response);
            return response.updateRecord;
        }

        public GraphMessage ReceiveMessage(GraphMessage message) {

            // instantiate full message
            GraphMessage fullMessage = new GraphMessage();

            bool fullMessageUpdated = true;
            // iteratively
            while (fullMessageUpdated == true) {
                // instantiate UpdateRecords
                UpdateRecord updateRecord = new UpdateRecord(); 
                // merge GraphMessage into full message
                fullMessageUpdated = fullMessage.MergeWith(message);
                // use MessageResponse to update UpdateRecords
                updateRecord.MergeWith(UpdateGraph(message));
                // use DeconflictRules on update record to generate GraphMessage
                message = ProcessRules(updateRecord, deconflictRules);
                // merge GraphMessage into full message
                fullMessageUpdated = fullMessageUpdated || fullMessage.MergeWith(message);
                // use MessageResponse to update UpdateRecords
                updateRecord.MergeWith(UpdateGraph(message));
                // use EffectRules on update record to generate GraphMessage... loop back
                message = ProcessRules(updateRecord, effectRules);
            }

            // return full message
            return fullMessage;
        }
    }
}