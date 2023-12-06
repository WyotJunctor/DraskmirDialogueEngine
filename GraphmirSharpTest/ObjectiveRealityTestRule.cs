namespace GraphmirSharpTest;

using Graphmir;
using Graphmir.GameObjects;
using Graphmir.GraphObjects;

public class ObjectiveRealityTestRule : ReferenceRule {
    public ObjectiveRealityTestRule(Graph graph, Vertex vert) : base(graph, vert) {}

    public override GraphMessage CheckRule(Vertex vert, EdgeUpdate edgeUpdate)
    {
        GraphMessage message = new GraphMessage();

        // validation stage
        if (graph.vertices.ContainsKey(new Label("c")) || !graph.vertices[edgeUpdate.src.vLabel].HasLabels(EngineConfig.primaryLabel, new Label("Instance")))
            return message;

        // execute rule
        message.addVerts.Add(new Label("c"));
        return message;
    }
}