namespace Graphmir.GraphObjects {
    public struct Label : IEquatable<Label> {
        public string value;

        public Label (string value) {
            this.value = value;
        }

        public static bool operator ==(Label obj1, Label obj2)
        {
            if (ReferenceEquals(obj1, obj2)) 
                return true;
            if (ReferenceEquals(obj1, null)) 
                return false;
            if (ReferenceEquals(obj2, null))
                return false;
            return obj1.Equals(obj2);
        }
        public static bool operator !=(Label obj1, Label obj2) => !(obj1 == obj2);

        public bool Equals(Label other)
        {
            if (ReferenceEquals(other, null))
                return false;
            if (ReferenceEquals(this, other))
                return true;
            return value == other.value;
        }

        public override bool Equals(object? obj)
        {
            return obj is Label && Equals((Label)obj);
        }

        public override int GetHashCode()
        {
            return value.GetHashCode();
        }
    }
}