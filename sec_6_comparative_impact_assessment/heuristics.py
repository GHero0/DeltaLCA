from classes import A_MORE, B_MORE, NOT_SURE

###################################### HEURISTICS V1 ######################################

# Rule 1: Die_Size (the size of the actual chip)
def Compare_Die_Size(IC_A, IC_B):
    if IC_A.Die_Size is None or IC_B.Die_Size is None:
        return NOT_SURE, f"No information about die size, IC_A: {IC_A.Die_Size}, IC_B: {IC_B.Die_Size}"
    if (IC_A.Die_Size - IC_B.Die_Size) > 0:
        return A_MORE, f"IC_A: {IC_A.Die_Size:.4f} > IC_B: {IC_B.Die_Size:.4f}"
    elif (IC_A.Die_Size - IC_B.Die_Size) < 0:
        return B_MORE, f"IC_A: {IC_A.Die_Size:.4f} < IC_B: {IC_B.Die_Size:.4f}"
    return NOT_SURE, f"IC_A: {IC_A.Die_Size:.4f} = IC_B: {IC_B.Die_Size:.4f}"

# Rule 2: Process Node
# Notes: Bigger process node means less advanced (e.g., 28nm is older than 7nm), has less fab carbon footprint 
def Compare_Process_Node(IC_A, IC_B):
    if IC_A.Process_Node is None or IC_B.Process_Node is None:
        return NOT_SURE, f"No information about process node, IC_A: {IC_A.Process_Node}, IC_B: {IC_B.Process_Node}"
    if (IC_A.Process_Node - IC_B.Process_Node) > 0:
        return B_MORE, f"IC_A: {IC_A.Process_Node} > IC_B: {IC_B.Process_Node}"
    elif (IC_A.Process_Node - IC_B.Process_Node) < 0:
        return A_MORE, f"IC_A: {IC_A.Process_Node} < IC_B: {IC_B.Process_Node}"
    return NOT_SURE, f"IC_A: {IC_A.Process_Node} = IC_B: {IC_B.Process_Node}"

# Rule 3: Power Consumption (Product Use Stage)
def Compare_Power_Consumption(IC_A, IC_B):
    if IC_A.Power_Consumption is None or IC_B.Power_Consumption is None:
        return NOT_SURE, f"No information about power consumption, IC_A: {IC_A.Power_Consumption}, IC_B: {IC_B.Power_Consumption}"
    if (IC_A.Power_Consumption - IC_B.Power_Consumption) > 0:
        return A_MORE, f"IC_A: {IC_A.Power_Consumption} > IC_B: {IC_B.Power_Consumption}"
    elif (IC_A.Power_Consumption - IC_B.Power_Consumption) < 0:
        return B_MORE, f"IC_A: {IC_A.Power_Consumption} < IC_B: {IC_B.Power_Consumption}"
    return NOT_SURE, f"IC_A: {IC_A.Power_Consumption} = IC_B: {IC_B.Power_Consumption}"

# Rule 4: Smallest Package Size
# Notes: if we don't know the die size, we can use the smallest package size of that specific model as a proxy
def Compare_Package_Size(IC_A, IC_B):
    if IC_A.Min_Package_Size is None or IC_B.Min_Package_Size is None:
        return NOT_SURE, f"No information about min package size, IC_A: {IC_A.Min_Package_Size}, IC_B: {IC_B.Min_Package_Size}"
    if (IC_A.Min_Package_Size - IC_B.Min_Package_Size) > 0:
        return A_MORE, f"IC_A: {IC_A.Min_Package_Size:.4f} > IC_B: {IC_B.Min_Package_Size:.4f}"
    elif (IC_A.Min_Package_Size - IC_B.Min_Package_Size) < 0:
        return B_MORE, f"IC_A: {IC_A.Min_Package_Size:.4f} < IC_B: {IC_B.Min_Package_Size:.4f}"
    return NOT_SURE, f"IC_A: {IC_A.Min_Package_Size:.4f} = IC_B: {IC_B.Min_Package_Size:.4f}"

heuristic_functions = [Compare_Die_Size, Compare_Power_Consumption, Compare_Package_Size, Compare_Process_Node]

###################################### HEURISTICS V2 ######################################
epa_slope= -0.0283
epa_intercept = 1.702
gpa_slope = -2.609
gpa_intercept = 168.207

def predict_value(slope, intercept, nm_value):
    # Calculate the estimated value for a given nanometer value
    return slope * nm_value + intercept

def nm_compare(node_A, node_B):
    # Calculate the ratio of the two nodes, return the relative percentage of IC_A/IC_B, IC_B is the baseline so is 1
    epa_ratio = predict_value(epa_slope, epa_intercept, node_A) / predict_value(epa_slope, epa_intercept, node_B)
    gpa_ratio = predict_value(gpa_slope, gpa_intercept, node_A) / predict_value(gpa_slope, gpa_intercept, node_B)
    # print(f"epa_ratio: {epa_ratio}, gpa_ratio: {gpa_ratio}")
    return (epa_ratio + gpa_ratio)/2

# Rule 1: Die (Die Size & Process Node)
def Compare_Effective_Die_Size(IC_A, IC_B):
    if IC_A.Die_Size is None or IC_B.Die_Size is None:
        return NOT_SURE, f"No information about die size, IC_A: {IC_A.Die_Size:.4f}, IC_B: {IC_B.Die_Size:.4f}"
    if IC_A.Process_Node is None or IC_B.Process_Node is None:
        return NOT_SURE, f"No information about process node, IC_A: {IC_A.Process_Node}, IC_B: {IC_B.Process_Node}"

    if IC_A.Process_Node == IC_B.Process_Node:
        process_node_ratio = 1
    else:
        process_node_ratio = nm_compare(IC_A.Process_Node, IC_B.Process_Node)

    # Calculate the effective Die_Size of IC_A minus the Die_Size of IC_B
    # if > 0: then A_MORE
    # if < 0: then B_MORE
    # if = 0: then A = B
    diff = IC_A.Die_Size*process_node_ratio - IC_B.Die_Size
    if diff > 0:
        return A_MORE, f"IC_A: {IC_A.Die_Size*process_node_ratio} > IC_B: {IC_B.Die_Size:.4f}"
    elif diff < 0:
        return B_MORE, f"IC_A: {IC_A.Die_Size*process_node_ratio} < IC_B: {IC_B.Die_Size:.4f}"
    return NOT_SURE, f"IC_A: {IC_A.Die_Size*process_node_ratio} = IC_B: {IC_B.Die_Size:.4f}"

heuristic_functions_v2 = [Compare_Effective_Die_Size, Compare_Power_Consumption]
