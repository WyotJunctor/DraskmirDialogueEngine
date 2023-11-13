namespace Graphmir {
    using Graphmir.GraphObjects;
    public class EngineConfig {
        public static HashSet<Label> primaryTypes = new HashSet<Label>() {new Label("Is"), new Label("Was")};

        public static Label primaryLabel = new Label("Is");

        public static Dictionary<Label, int> labelPriority = new Dictionary<Label, int>() {
            {new Label("Is"), 0},
            {new Label("Was"), 1},
        };
    }
}