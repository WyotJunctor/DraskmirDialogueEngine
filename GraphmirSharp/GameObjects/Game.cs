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

        // TODO implement and include rule map templates when spawning entities
        public void SpawnEntity(GraphMessage baseConceptMap, GraphMessage spawnMessage) {
            Entity entity = new Entity(baseConceptMap);
            ProcessMessage(spawnMessage);
            entity.ObserveSpawn(objReality.GetVisibleGraph(entity.egoLabel));
        }
    }
}