namespace Graphmir.GameObjects {
    using GraphObjects;

    public class Reality {

        public Graph graph;
        // structure which maps vertices to rules
        public RuleMap deconflictRules = new RuleMap();
        public RuleMap effectRules = new RuleMap();

        public Reality(
            GraphMessage baseConceptMap,
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap)
        {
            graph = new Graph();
            GraphMessage baseVerts = new GraphMessage();
            baseVerts.addVerts = baseConceptMap.addVerts;
            ReceiveMessage(baseVerts);
            InstantiateRules(deconflictRuleFactoryMap, deconflictRules);
            InstantiateRules(effectRuleFactoryMap, effectRules);
            GraphMessage baseEdges = new GraphMessage();
            baseEdges.addEdges = baseConceptMap.addEdges;
            ReceiveMessage(baseEdges);
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
            }
            foreach (var keyPair in response.labelAddMap) {
                Vertex vert = keyPair.Key;
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
                if (fullMessageUpdated == false)
                    break;
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