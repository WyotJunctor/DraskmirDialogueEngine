namespace GraphmirSharpTest;
using Graphmir.GraphObjects;

[TestClass]
public class GraphTest
{
    [TestMethod]
    public void UpdateTest()
    {
        Graph graph = new();

        Label label = new("test_label");
        Vertex vertex = new(label);

        GraphMessage message1 = new() {
            addVerts = {
                label
            }
        };

        MessageResponse response = graph.UpdateFrom(message1);
        Assert.IsTrue(response.labelAddMap.ContainsKey(vertex));
    }
}