namespace Graphmir {
    using GraphObjects;

    public class Clock {
        public static uint globalTimestamp;
    }

    public class Rule {
        public virtual GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate) {
            return new GraphMessage();
        } 

        public virtual Rule AddRule(Vertex vert) {
            return this;
        }

        public override int GetHashCode()
        {
            // todo get hash code correctly for checking when to remove rule
            return base.GetHashCode();
        }
    }

    public class CopyRule : Rule {
        // todo, when added, return a copy of this rule
        public override Rule AddRule(Vertex vert)
        {
            return new CopyRule();
        }
    }

    public class ReferenceRule : Rule {
        // todo, when added, return reference to original rule
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

        public void DeleteRule(Vertex vert, Label label) {
            inheritedRules[vert.vLabel].ExceptWith(inherentRules[label]);
        }

        public void AddRule(Vertex vert, Label label) {
            foreach (var rule in inherentRules[label]) {
                inheritedRules[vert.vLabel].Add(rule.AddRule(vert));
            }
        }
    }

    public class Reality {

        Graph graph;
        // structure which maps vertices to rules
        RuleMap deconflictRules = new RuleMap();
        RuleMap effectRules = new RuleMap();
        RuleMap spawnRules = new RuleMap();

        public Reality(GraphMessage baseConceptMap) {
            graph = new Graph();
            graph.UpdateFrom(baseConceptMap);
            // TODO, receive rule map templates and instantiate them
        }

        GraphMessage ProcessRules(UpdateRecord updateRecord, RuleMap ruleMap) {
            GraphMessage message = new GraphMessage();
            // iterate over rules of src, tgt, refVert, and invRefVert?
            // check rules and merge into graph message
            foreach (var edgeUpdate in updateRecord.edges) {
                message.MergeWith(ruleMap.CheckRule(edgeUpdate.src, edgeUpdate));
                message.MergeWith(ruleMap.CheckRule(edgeUpdate.tgt, edgeUpdate));
                message.MergeWith(ruleMap.CheckRule(edgeUpdate.refVert, edgeUpdate));
                message.MergeWith(ruleMap.CheckRule(edgeUpdate.invRefVert, edgeUpdate));
            }
            // return graph message
            return message;
        }

        void PropagateRules(MessageResponse response) {
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

        UpdateRecord UpdateGraph(GraphMessage message) {
            // process GraphMessage and produce MessageResponse
            MessageResponse response = graph.UpdateFrom(message);
            // use MessageResponse.labelAddMap and labelDelMap to handle rule propagation
            PropagateRules(response);
            return response.updateRecord;
        }

        public GraphMessage ReceiveSpawnMessage(GraphMessage message) {
            GraphMessage fullMessage = message;
            UpdateRecord updateRecord = UpdateGraph(message);
            fullMessage.MergeWith(ProcessRules(updateRecord, spawnRules));
            return ReceiveMessage(fullMessage);
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

    public class ObjectiveReality : Reality {

        public ObjectiveReality(GraphMessage baseConceptMap) : base(baseConceptMap) {}
        public GraphMessage GetVisibleGraph(Label label) {
            return new GraphMessage();
        }
    }
}