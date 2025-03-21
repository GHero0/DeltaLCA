from ortools.linear_solver import pywraplp
import numpy as np
import os
import argparse

from heuristics import heuristic_functions, heuristic_functions_v2
from classes import *
from utils import *

# return a list of pairs of conflicting heuristic ids
def conflicting_heuristics(heuristics):
    conflicting_h_ids = []
    # ignore all heuristics for which we can find a counterexample heuristic
    # TODO: make this robust to Sets when we will have Set-heuristics
    for h_i, h in enumerate(heuristics):
        if h.direction == NOT_SURE:
            continue
        for counter_h_i, counter_h in enumerate(heuristics):
            if h_i == counter_h_i or counter_h.direction == NOT_SURE:
                continue
            if h.parts_a[0] == counter_h.parts_a[0] and h.parts_b[0] == counter_h.parts_b[0] and h.direction == -counter_h.direction:
                conflicting_h_ids.append([h_i, counter_h_i])
    return conflicting_h_ids

# proof_direction = A_MORE if we want to show that A > B.
# right now, we should just switch the designs
def select_heuristics(heuristics, filter_out_conflicts=True, prove_direction=A_MORE, use_carbon_footprint=True,
                      a_indices=[], b_indices=[], footprints_a=[], footprints_b=[]):
    prob = pywraplp.Solver.CreateSolver('SAT_INTEGER_PROGRAMMING')
    prob.SuppressOutput()
    if not prob:
        print("The OR-Tools solver could not be created. Check your installation")
        exit()
    #print(a_indices)
    #print(b_indices)
    b_variables = [prob.IntVar(0,1,"b_"+str(i)) for i in b_indices]
    #print(b_variables)
    h_indices = list(range(len(heuristics)))
    #print(h_indices)
    h_variables = [prob.IntVar(0,1,"h_"+str(i)) for i in h_indices]
    #print(h_variables)
    if use_carbon_footprint:
        ca_variables = [prob.IntVar(0,1,"ca_"+str(i)) for i in a_indices]
        cb_variables = [prob.IntVar(0,1,"cb_"+str(i)) for i in b_indices]

    # Filter out conflicting heuristics
    ignore_h_ids = []
    for h_i, h in enumerate(heuristics):
        if h.direction != prove_direction:
            ignore_h_ids.append(h_i)
    if filter_out_conflicts:
        conflicting_h_ids = conflicting_heuristics(heuristics)
        ignore_h_ids += [c[0] for c in conflicting_h_ids]
    ignore_h_ids = np.unique(ignore_h_ids)
    #print("Filtered out heuristics:")
    #print(ignore_h_ids)

    # add constraints
    # 1) Each a_i can only be used once
    for a_i in a_indices:
        a_i_sum = []
        for h_i, h in enumerate(heuristics):
            if filter_out_conflicts and h_i in ignore_h_ids and not heuristics[h_i].user_defined:
                continue
            if a_i in h.parts_a:
                a_i_sum.append(h_variables[h_i])
        #print(a_i_sum)
        if use_carbon_footprint:
            prob.Add(sum(a_i_sum) <= 1 - ca_variables[a_i])
        else:
            prob.Add(sum(a_i_sum) <= 1)

    # 2) Count b_i only if we have at least one heuristic for it
    for b_i in b_indices:
        b_i_sum = []
        for h_i, h in enumerate(heuristics):
            if filter_out_conflicts and h_i in ignore_h_ids and not heuristics[h_i].user_defined:
                continue
            if b_i in h.parts_b:
                b_i_sum.append(h_variables[h_i])
        #print(b_i_sum)
        if use_carbon_footprint:
            prob.Add(b_variables[b_i] <= sum(b_i_sum) + cb_variables[b_i])
        else:
            prob.Add(b_variables[b_i] <= sum(b_i_sum))

    # Turn off all ignored heuristics (except user-defined ones)
    for h_i in ignore_h_ids:
        if heuristics[h_i].user_defined:
            continue
        prob.Add(h_variables[h_i] == 0)
    # Turn on all user-defined heuristics
    for h_i in range(len(heuristics)):
        if heuristics[h_i].user_defined:
            prob.Add(h_variables[h_i] == 1)

    # the carbon footprint of A should be greater than the carbon footprint of B
    if use_carbon_footprint:
        footprint_a = 0
        for a_i in a_indices:
            if footprints_a[a_i] == None:
                prob.Add(ca_variables[a_i] == 0)
            else:
                #print(footprints_a[a_i])
                #print(ca_variables[a_i])
                footprint_a += footprints_a[a_i]*ca_variables[a_i]
        footprint_b = 0
        for b_i in b_indices:
            if footprints_b[b_i] == None:
                prob.Add(cb_variables[b_i] == 0)
            else:
                #print(footprints_b[b_i])
                #print(cb_variables[b_i])
                footprint_b += footprints_b[b_i]*cb_variables[b_i]
        if prove_direction == A_MORE:
            prob.Add(footprint_a >= footprint_b)
        elif prove_direction == B_MORE:
            prob.Add(footprint_a <= footprint_b)

    # Objective function
    obj_expr = sum(b_variables)
    # print(prob.NumVariables(), "variables created")
    # print(len(heuristics), "heuristics available")
    # print(len(b_variables) + len(h_variables) + len(ca_variables) + len(cb_variables), "integer variables created")
    # print(prob.NumConstraints(), "constraints created")
    # print(len(a_indices), "parts in A")
    # print(len(b_indices), "parts in B")

    prob.Maximize(obj_expr)
    # prob.SetNumThreads(8)
    status = prob.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        #print("Solver status:", status)
        best_obj = prob.Objective().Value()
        #print("best_obj value", best_obj)
        # print("Selected variables")
        #print("b_variables")
        #for v in b_variables:
        #    if np.isclose(v.solution_value(), 1.0):
        #        print(v, v.solution_value())
        #print("h_variables")
    else:
        raise Exception("Solver status:", status)

    selected_heuristics = []
    for v in h_variables:
        if np.isclose(v.solution_value(), 1.0):
            selected_heuristics.append(heuristics[int(v.name().split("_")[1])])
    selected_footprints_a = []
    selected_footprints_b = []
    if use_carbon_footprint:
        for v in ca_variables:
            if np.isclose(v.solution_value(), 1.0):
                selected_footprints_a.append(int(v.name().split("_")[1]))
        for v in cb_variables:
            if np.isclose(v.solution_value(), 1.0):
                selected_footprints_b.append(int(v.name().split("_")[1]))

    return selected_heuristics, selected_footprints_a, selected_footprints_b

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Integer program for LCA-for-PCB')
    parser.add_argument('--example_folder', type=str, default="Arduino_PCB_design_files")
    parser.add_argument('--design_A', type=str, default="PCB_summary_Leonardo_Rev3d.json")
    parser.add_argument('--design_B', type=str, default="PCB_summary_MKR1200.json")
    parser.add_argument('--use_v2', action='store_true', default=False)
    parser.add_argument('--prove_direction', type=str, default="A_MORE")
    parser.add_argument('--use_carbon_footprint', action='store_true', default=False)
    args = parser.parse_args()

    # Create IC instances after extracting and processing Die_Size
    print("ICs:")
    print("Design A:")
    ics_a = load_design(os.path.join(args.example_folder, args.design_A))
    print("Design B:")
    ics_b = load_design(os.path.join(args.example_folder, args.design_B))

    # pre-compute heuristics
    heuristics = []
    h_functions = heuristic_functions_v2 if args.use_v2 else heuristic_functions
    for i, ic_a in enumerate(ics_a):
        for j, ic_b in enumerate(ics_b):
            for h in h_functions:
                heuristics.append(Heuristic(ic_a, ic_b, h))

    print("Binary Integer Program:")
    # construct variables
    a_indices = [ic_a.id for ic_a in ics_a]
    b_indices = [ic_b.id for ic_b in ics_b]
    footprints_a = [ic_a.Carbon_Footprint for ic_a in ics_a]
    footprints_b = [ic_b.Carbon_Footprint for ic_b in ics_b]
    prove_direction = A_MORE if args.prove_direction == "A_MORE" else B_MORE if args.prove_direction == "B_MORE" else NOT_SURE
    selected_heuristics, selected_footprints_a, selected_footprints_b = select_heuristics(
        heuristics, filter_out_conflicts=True, prove_direction=prove_direction, use_carbon_footprint=args.use_carbon_footprint,
        a_indices=a_indices, b_indices=b_indices, footprints_a=footprints_a, footprints_b=footprints_b)

    # Final print
    print("Selected Heuristics:")
    for h in selected_heuristics:
        print(h)
    unmatched_summary, covered_parts_A, covered_parts_B, (ncA, ncB) = format_results(
        selected_heuristics, selected_footprints_a, selected_footprints_b, ics_a, ics_b)
    print(covered_parts_A)
    print(covered_parts_B)
    print(unmatched_summary)

    if args.use_carbon_footprint:
        print("Carbon footprint selection")
        print("Carbon footprint A:", np.sum([footprints_a[i] for i in selected_footprints_a]))
        print("Carbon footprint B:", np.sum([footprints_b[i] for i in selected_footprints_b]))
        print("Footprint selected parts A:", selected_footprints_a)
        print("Footprint selected parts B:", selected_footprints_b)