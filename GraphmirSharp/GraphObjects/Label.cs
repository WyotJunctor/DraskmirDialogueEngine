namespace Graphmir.GraphObjects {
    public class Label {
        public int value;

        public Label (int value) {
            this.value = value;
        }

        public override bool Equals(object? obj)
        {
            return obj is Label label && value == label.value;
        }

        public override int GetHashCode()
        {
            return value;
        }
    }
}