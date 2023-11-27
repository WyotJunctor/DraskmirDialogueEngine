using System.Dynamic;
using Graphmir.GraphObjects;

namespace Graphmir.GameObjects {
    public class Game {
        ObjectiveReality objReality;
        HashSet<Entity> entities;

        public void Step() {

            // NOTE(Simon): isn't there a way to oneline this?
            //              I know how I'd do it in Java...
            //              maybe uses LINQ? stinky...
            GraphMessage actionsMessage = new GraphMessage();
            foreach (Entity entity in entities) {
                actionsMessage.MergeWith(entity.ChooseAction());
            }

        }

        public void ProcessMessage(GraphMessage message) {
            GraphMessage resultsMessage = objReality.ReceiveMessage(message);

            foreach (Entity entity in entities) {
                entity.Observe(resultsMessage);
            }
        }

        public void SpawnEntity(
            GraphMessage baseConceptMap, 
            GraphMessage spawnMessage, 
            Dictionary<Label, List<RuleFactory>> deconflictRuleFactoryMap, 
            Dictionary<Label, List<RuleFactory>> effectRuleFactoryMap,
            Dictionary<Label, List<RuleFactory>> spawnRuleFactoryMap) 
        {
            Entity entity = new Entity(baseConceptMap, deconflictRuleFactoryMap, effectRuleFactoryMap, spawnRuleFactoryMap);
            ProcessMessage(spawnMessage);
            entity.ObserveSpawn(objReality.GetVisibleGraph(entity.subjReality.egoLabel));
            if (entity.subjReality.egoLabel != null)
            {
                entities.Add(entity);
            }
        }
    }
}