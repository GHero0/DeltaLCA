import networkx as nx

NOT_SURE = 0
A_MORE = 1
B_MORE = -1

# carbon footprint value prediction
epa_slope= -0.0283
epa_intercept = 1.702
gpa_slope = -2.609
gpa_intercept = 168.207

def predict_value(slope, intercept, nm_value):
    # Calculate the estimated value for a given nanometer value
    return slope * nm_value + intercept

class IC:
    def __init__(self, dict_design, parts_id):
        self.jsondata = dict_design
        self.jsondata["Count"] = 1

        self.id = parts_id
        self.Name = dict_design["Name"]

        self.Die_Size = None
        if "Die_Size" in dict_design:
            if type(dict_design["Die_Size"]) == str:
                length, width = map(lambda x: float(x.replace("mm", "")), dict_design["Die_Size"].split(" x "))
                self.Die_Size = length*width
            elif type(dict_design["Die_Size"]) == float:
                self.Die_Size = dict_design["Die_Size"]
            if self.Die_Size == float("inf"):
                self.Die_Size = None

        self.Power_Consumption = None
        if "Power_Consumption" in dict_design and dict_design["Power_Consumption"] != "":
            self.Power_Consumption = float(dict_design["Power_Consumption"])
            if self.Power_Consumption == float("inf"):
                self.Power_Consumption = None

        self.Min_Package_Size = None
        if "Package_Area" in dict_design:
            length, width = map(lambda x: float(x.replace("mm", "")), dict_design["Package_Area"].split(" x "))
            self.Min_Package_Size = length*width
        if "Min_Package_Size" in dict_design:
            length, width = map(lambda x: float(x.replace("mm", "")), dict_design["Min_Package_Size"].split(" x "))
            self.Min_Package_Size = length*width
        if self.Min_Package_Size == float("inf"):
            self.Min_Package_Size = None

        self.Process_Node = None
        if "Process_Node" in dict_design and dict_design["Process_Node"] != "":
            self.Process_Node = float(dict_design["Process_Node"].split(" nm")[0])

        self.GPIO_Count = None
        if "GPIO_Count" in dict_design and dict_design["GPIO_Count"] is not None and dict_design["GPIO_Count"] != "":
            self.GPIO_Count = int(dict_design["GPIO_Count"])

        self.Memory_Size = None
        if "Memory_Size" in dict_design:
            self.Memory_Size = dict_design["Memory_Size"]

        self.Carbon_Footprint = None
        if self.Process_Node != None and self.Die_Size != None:
            self.Carbon_Footprint = abs(predict_value(epa_slope, epa_intercept, self.Process_Node))
        if "Carbon_Footprint" in dict_design:
            self.Carbon_Footprint = float(dict_design["Carbon_Footprint"])
        elif self.Carbon_Footprint is not None:
            self.jsondata["Carbon_Footprint"] = self.Carbon_Footprint

    def __str__(self) -> str:
        return f"id: {self.id}; name: {self.Name}; Die_Size: {self.Die_Size} mm^2; " \
            f"Power_Consumption: {self.Power_Consumption}; " \
            f"Min_Package_Size: {self.Min_Package_Size} mm^2; Process_Node: {self.Process_Node}"

    def __repr__(self) -> str:
        return self.__str__()

class Heuristic:
    def __init__(self, ics_a, ics_b, heuristic_function, is_user_defined=False):
        if type(ics_a) == list:
            self.parts_a = [ic_a.id for ic_a in ics_a]
            self.parts_a_names = [ic_a.Name for ic_a in ics_a]
        else:
            self.parts_a = [ics_a.id]
            self.parts_a_names = [ics_a.Name]
        if type(ics_b) == list:
            self.parts_b = [ic_b.id for ic_b in ics_b]
            self.parts_b_names = [ic_b.Name for ic_b in ics_b]
        else:
            self.parts_b = [ics_b.id]
            self.parts_b_names = [ics_b.Name]
        self.direction, self.explanation = heuristic_function(ics_a, ics_b)
        self.heuristic_name = heuristic_function.__name__
        self.user_defined = is_user_defined
    
    def __str__(self) -> str:
        return f"parts_a: {self.parts_a}; parts_b: {self.parts_b}; direction: {self.direction}; "\
             f"heuristic_name: {self.heuristic_name} (Explanation: {self.explanation})"

class HeuristicsGraph:
    def __init__(self, heuristics):
        self.heuristics = heuristics
        self.g = nx.Graph()
        self.edge_labels = {}
        for h in heuristics:
            if h.direction == A_MORE:
                for p_a in h.parts_a:
                    a_name = "a_"+str(p_a)
                    self.g.add_nodes_from([a_name], bipartite=0)
                    for p_b in h.parts_b:
                        b_name = "b_"+str(p_b)
                        self.g.add_nodes_from([b_name], bipartite=1)
                        self.g.add_edges_from([(a_name, b_name)])
                        self.edge_labels[(a_name, b_name)] = str(h.direction)
            elif h.direction == B_MORE:
                for p_a in h.parts_a:
                    a_name = "a_"+str(p_a)
                    self.g.add_nodes_from([a_name], bipartite=0)
                    for p_b in h.parts_b:
                        b_name = "b_"+str(p_b)
                        self.g.add_nodes_from([b_name], bipartite=1)
                        self.g.add_edges_from([(b_name, a_name)])
                        self.edge_labels[(b_name, a_name)] = str(h.direction)
        #print(nx.is_bipartite(self.g))
        #print(self.g.nodes)
    
    def draw_graph(self):
        top = nx.bipartite.sets(self.g)[0]
        pos = nx.bipartite_layout(self.g, top)

        nx.draw(self.g, pos)
        nx.draw_networkx_edge_labels(self.g, pos, self.edge_labels)
