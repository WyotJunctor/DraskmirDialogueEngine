namespace Graphmir.GameObjects {
    using Graphmir.GraphObjects;
    public class Entity {
        Label egoLabel;
        Reality subjReality;
        ChooseMaker chooseMaker;

        public void Observe(GraphMessage eventsMessage) {
            subjReality.ReceiveMessage(eventsMessage);
        }

        public GraphMessage ChooseAction() {
            return chooseMaker.MakeChoose(egoLabel, subjReality);
        }
    }
}