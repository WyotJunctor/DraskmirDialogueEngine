using System.Dynamic;
using Graphmir.GraphObjects;

namespace Graphmir.GameObjects {
    public class Game {
        Reality objReality;
        HashSet<Entity> entities;

        public void Step() {

            // NOTE(Simon): isn't there a way to oneline this?
            //              I know how I'd do it in Java...
            //              maybe uses LINQ? stinky...
            GraphMessage actionsMessage = new GraphMessage();
            foreach (Entity entity in entities) {
                actionsMessage.UpdateFrom(entity.ChooseAction());
            }

            GraphMessage resultsMessage = objReality.ReceiveMessage(actionsMessage);

            foreach (Entity entity in entities) {
                entity.Observe(resultsMessage);
            }

        }
    }
}