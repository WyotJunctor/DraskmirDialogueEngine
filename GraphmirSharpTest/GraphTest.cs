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

        GraphMessage message1 = new() {
            addVerts = {
                label
            }
        };

        MessageResponse response = graph.UpdateFrom(message1);
        Assert.IsTrue(response.labelAddMap.Count == 1);
        foreach (var vert_pair in response.labelAddMap) {
            Assert.IsTrue(vert_pair.Key.vLabel == label);
        }
    }
}