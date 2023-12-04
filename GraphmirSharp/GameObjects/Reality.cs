namespace Graphmir {
    using GraphObjects;

    public class Clock {
        public static uint globalTimestamp;
    }

    public class Rule {

        protected Graph graph;
        protected Vertex vert;

        public Rule(Graph graph, Vertex vert) {
            this.graph = graph;
            this.vert = vert;
        }

        public virtual GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate) {
            return new GraphMessage();
        }

        public virtual Rule AddRule(Vertex vert) {
            return this;
        }
    }

    public class ReferenceRule : Rule {
        public ReferenceRule(Graph graph, Vertex vert) : base(graph, vert) {}
    }

    public class CopyRule : Rule {

        public CopyRule(Graph graph, Vertex vert) : base(graph, vert) {}

        public override Rule AddRule(Vertex vert)
        {
            return new CopyRule(graph, vert);
        }

        public override int GetHashCode()
        {
            return GetType().GetHashCode();
        }
    }

    public class RuleMap {
        public DefaultDictionary<Label, HashSet<Rule>> inherentRules = new DefaultDictionary<Label, HashSet<Rule>>();
        public DefaultDictionary<Label, HashSet<Rule>> inheritedRules = new DefaultDictionary<Label, HashSet<Rule>>();

        public GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate) {
            GraphMessage message = new GraphMessage();
            if (vert != null) {
                foreach (var rule in inheritedRules.TryGet(vert.vLabel)) {
                    message.MergeWith(rule.CheckRule(vert, edgeUpdate));
                }
            }
            return message;
        }

        public GraphMessage CheckRules(UpdateRecord updateRecord) {
            GraphMessage message = new GraphMessage();
            // iterate over rules of src, tgt, refVert, and invRefVert?
            // check rules and merge into graph message
            foreach (var edgeUpdate in updateRecord.edges) {
                message.MergeWith(CheckRule(edgeUpdate.src, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.tgt, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.refVert, edgeUpdate));
                message.MergeWith(CheckRule(edgeUpdate.invRefVert, edgeUpdate));
            }
            // return graph message
            return message;
        }

        public void DeleteRule(Vertex vert, Label label) {
            inheritedRules[vert.vLabel].ExceptWith(inherentRules[label]);
        }

        public void AddRule(Vertex vert, Label label) {
            foreach (var rule in inherentRules[label]) {
                inheritedRules[vert.vLabel].Add(rule.AddRule(vert));
            }
        }
    }

    public delegate Rule RuleFactory(Graph graph, Vertex vert);

    public class Reality {

        protected Graph graph;
        // structure which maps vertices to rules
        RuleMap deconflictRules = new RuleMap();
        RuleMap effectRules = new RuleMap();

        public Reality(
            GraphMessage baseConceptMap,
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap)
        {
            graph = new Graph();
            graph.UpdateFrom(baseConceptMap);
            InstantiateRules(deconflictRuleFactoryMap, deconflictRules);
            InstantiateRules(effectRuleFactoryMap, effectRules);
        }

        public void InstantiateRules(Dictionary<Label, List<RuleFactory>> ruleFactoryMap, RuleMap ruleMap) {
            foreach (var keyPair in ruleFactoryMap) {
                foreach (var ruleFactory in keyPair.Value) {
                    ruleMap.inherentRules[keyPair.Key].Add(ruleFactory(graph, graph.vertices[keyPair.Key]));
                }
            }
        }

        protected void PropagateRules(MessageResponse response) {
            foreach (var keyPair in response.labelDelMap) {
                Vertex vert = keyPair.Key;
                foreach (Label label in response.labelDelMap[vert].labels.TryGet(EngineConfig.primaryLabel)) {
                    deconflictRules.DeleteRule(vert, label);
                    effectRules.DeleteRule(vert, label);
                }
                foreach (Label label in response.labelAddMap[vert].labels.TryGet(EngineConfig.primaryLabel)) {
                    deconflictRules.AddRule(vert, label);
                    effectRules.AddRule(vert, label);
                }
            }
        }

        protected UpdateRecord UpdateGraph(GraphMessage message) {
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
                message = deconflictRules.CheckRules(updateRecord);
                // merge GraphMessage into full message
                fullMessageUpdated = fullMessageUpdated || fullMessage.MergeWith(message);
                // use MessageResponse to update UpdateRecords
                updateRecord.MergeWith(UpdateGraph(message));
                // use EffectRules on update record to generate GraphMessage... loop back
                message = effectRules.CheckRules(updateRecord);
            }

            // return full message
            return fullMessage;
        }
    }

    public class ObjectiveReality : Reality {

        public ObjectiveReality(
            GraphMessage baseConceptMap,
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap) : base(baseConceptMap, deconflictRuleFactoryMap, effectRuleFactoryMap) {}
        public GraphMessage GetVisibleGraph(Label label) {
            return new GraphMessage();
        }
    }

    public class SubjectiveReality : Reality {
        RuleMap spawnRules = new RuleMap();

        public Label egoLabel;

        public SubjectiveReality(
            GraphMessage baseConceptMap,
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> spawnRuleFactoryMap) : base(baseConceptMap, deconflictRuleFactoryMap, effectRuleFactoryMap) {
                InstantiateRules(spawnRuleFactoryMap, spawnRules);
            }

        public GraphMessage ReceiveSpawnMessage(GraphMessage message) {
            GraphMessage fullMessage = message;
            UpdateRecord updateRecord = UpdateGraph(message);
            fullMessage.MergeWith(spawnRules.CheckRules(updateRecord));

            egoLabel = GetEgoLabel();
            return ReceiveMessage(fullMessage);
        }

        public Label? GetEgoLabel() {
            Vertex? egoInstance = graph.vertices[new Label("Ego")].QueryNeighborhoodVertex(
                QueryTargetType.TgtVert, 
                EdgeDirection.Ingoing, 
                refVertLabels:new HashSet<Label>() {EngineConfig.primaryLabel}, 
                tgtVertLabels:new HashSet<Label>() {new Label("Instance")}).FirstOrDefault();
            if (egoInstance == null) {
                return null;
            }
            return egoInstance.vLabel;
        }
    }
}