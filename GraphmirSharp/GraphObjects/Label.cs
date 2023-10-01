namespace Graphmir.GraphObjects {
    public class Label {
        public int Value;

        public Label (int value) {
            this.Value = value;
        }

        public override bool Equals(object? obj)
        {
            return (obj is Label) && Value == ((Label)obj).Value;
        }

        public override int GetHashCode()
        {
            return Value;
        }
    }
}