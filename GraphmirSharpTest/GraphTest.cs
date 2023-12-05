namespace GraphmirSharpTest;
using Graphmir.GraphObjects;
using Graphmir.GameObjects;

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

    [TestMethod]
    public void HelloRealityTest() {
        GraphMessage objectiveConceptMap = Game.JSONToGraphMessage("C:\\Users\\Wyatt Joyner\\Projects\\Graphmir\\DraskmirDialogueEngine\\GraphmirSharpTest\\ObjectiveRealityConceptMapTest.json");
        ObjectiveReality reality = new(objectiveConceptMap, new(), new());
        // check if correct number of vertices and edges exist
        Assert.AreEqual(3, reality.graph.vertices.Count);
        // check labels of particular vertices
        // print b's labels
        // Console.WriteLine(reality.graph.vertices[new("b")].labels.labels.TryGet(new ("Is")).Count);
        Assert.IsTrue(reality.graph.vertices[new("b")].HasLabel(new("Is"), new("a")));
    }
}