namespace Graphmir.GraphObjects {

    public class Vertex {
        public readonly Label vLabel;
        public uint LastUpdated;
        LocalIndex localIndex;

        public Vertex(Label vLabel, uint lastUpdated) {
            this.vLabel = vLabel;
            this.LastUpdated = lastUpdated;
            this.localIndex = new LocalIndex(); 
        }
    }
}