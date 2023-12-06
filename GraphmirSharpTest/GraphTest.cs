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
        Dictionary<Label, List<RuleFactory>> effectRules = new Dictionary<Label, List<RuleFactory>>() {
            {
                new("a"), 
                new() {
                    delegate (Graph graph, Vertex vert) {return new ObjectiveRealityTestRule(graph, vert);}
                }
            }
        };
        ObjectiveReality reality = new ObjectiveReality(objectiveConceptMap, new(), effectRules);

        // check if correct number of vertices and edges exist
        Assert.AreEqual(4, reality.graph.vertices.Count);
        // check labels of particular vertices
        Assert.IsTrue(reality.graph.vertices[new("b")].HasLabels(new Label("Is"), new Label("a")));

        GraphMessage message = new GraphMessage();
        message.addVerts.Add(new("d"));
        message.addEdges.Add(new Edge<Label>(new("d"), new("b"), new("Is")));
        message.addEdges.Add(new Edge<Label>(new("d"), new("Instance"), new("Is")));
        reality.ReceiveMessage(message);

        Assert.IsTrue(reality.graph.vertices.ContainsKey(new("c")));
    }
}