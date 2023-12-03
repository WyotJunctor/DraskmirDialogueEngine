namespace Graphmir.GameObjects {
    using Graphmir.GraphObjects;
    public class Entity {
        public SubjectiveReality subjReality;
        ChooseMaker chooseMaker;

        public Entity(
            SubjectiveReality reality, ChooseMaker chooseMaker)
        {
            subjReality = reality;
            this.chooseMaker = chooseMaker;
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