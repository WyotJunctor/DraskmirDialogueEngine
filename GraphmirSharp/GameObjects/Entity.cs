namespace Graphmir.GameObjects {
    using Graphmir.GraphObjects;
    public class Entity {
        public SubjectiveReality subjReality;
        ChooseMaker chooseMaker;
        
        public Entity(
            GraphMessage baseConceptMap,             
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap, 
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> spawnRuleFactoryMap) 
        {
            subjReality = new SubjectiveReality(baseConceptMap, deconflictRuleFactoryMap, effectRuleFactoryMap, spawnRuleFactoryMap);
        }

        public GraphMessage ObserveSpawn(GraphMessage message) {
            return subjReality.ReceiveSpawnMessage(message);
        }

        public void Observe(GraphMessage eventsMessage) {
            subjReality.ReceiveMessage(eventsMessage);
        }

        public GraphMessage ChooseAction() {
            return chooseMaker.MakeChoose(subjReality);
        }
    }
}