namespace Graphmir.GameObjects {
    using Graphmir.GraphObjects;
    public class Entity {
        public Label egoLabel;
        Reality subjReality;
        ChooseMaker chooseMaker;

        // todo include rule map templates when spawning
        // todo fetch egoLabel
        public Entity(GraphMessage baseConceptMap) {
            subjReality = new Reality(baseConceptMap);
        }

        public void ObserveSpawn(GraphMessage message) {
            subjReality.ReceiveSpawnMessage(message);
        }

        public void Observe(GraphMessage eventsMessage) {
            subjReality.ReceiveMessage(eventsMessage);
        }

        public GraphMessage ChooseAction() {
            return chooseMaker.MakeChoose(egoLabel, subjReality);
        }
    }
}