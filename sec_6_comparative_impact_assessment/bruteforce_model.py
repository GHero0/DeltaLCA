import os
import itertools
import argparse

from heuristics import heuristic_functions, heuristic_functions_v2
from classes import *
from utils import *
from ortools_model import conflicting_heuristics

def verify_proposition(heuristics, nA, nB, proposition=A_MORE):
    if len(heuristics) == 0:
        return False # or vacuously true?
    if proposition == A_MORE:
        from_parts = [p for h in heuristics for p in h.parts_a]
        unique_from_parts = set(from_parts)
        # check that from parts are not used more than once
        if len(unique_from_parts) != len(from_parts):
            return False
        to_parts = set([p for h in heuristics for p in h.parts_b])
        # and that the to parts covered the entire set
        return len(unique_from_parts) <= nA and len(to_parts) == nB
    elif proposition == B_MORE:
        from_parts = [p for h in heuristics for p in h.parts_b]
        unique_from_parts = set(from_parts)
        if len(unique_from_parts) != len(from_parts):
            return False
        to_parts = set([p for h in heuristics for p in h.parts_a])
        return len(unique_from_parts) <= nB and len(to_parts) == nA
    elif proposition == NOT_SURE:
        raise Exception("ERROR: proposition NOT_SURE cannot be verified")
    else:
        raise Exception("ERROR: unknown proposition")

def list_to_num(l):
    return sum([2**i for i, e in enumerate(l) if e == 1])

def brute_force_search(filtered_heuristics, nA, nB, nH, prove_direction=A_MORE, break_early=True):
    result_set = []
    for selection in itertools.product([0, 1], repeat=nH):
        selected_heuristics = [h for i, h in enumerate(filtered_heuristics) if selection[i] == 1]
        if verify_proposition(selected_heuristics, nA, nB, prove_direction):
            print(f"    Found solution {list_to_num(selection)}/{2**nH}")
            if break_early:
                return [selected_heuristics]
            else:
                result_set.append(selected_heuristics)
    return result_set

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Brute force search for LCA-for-PCB')
    parser.add_argument('--example_folder', type=str, default="Arduino_PCB_design_files")
    parser.add_argument('--design_A', type=str, default="PCB_summary_Leonardo_Rev3d.json")
    parser.add_argument('--design_B', type=str, default="PCB_summary_MKR1200.json")
    parser.add_argument('--prove_direction', type=str, default="A_MORE")
    parser.add_argument('--use_v2', action='store_true', default=False)
    parser.add_argument('--break_early', action='store_true', default=False)
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

    print("Heuristics:")
    if len(heuristics) < 100:
        for h in heuristics:
            print(h)
    else:
        print(len(heuristics))

    print("Remove heuristics that prove the wrong direction:")
    prove_direction = A_MORE if args.prove_direction == "A_MORE" else B_MORE if args.prove_direction == "B_MORE" else NOT_SURE
    wrong_direction_h_ids = [i for i, h in enumerate(heuristics) if h.direction != prove_direction]

    print("Remove conflicting heuristics:")
    heuristic_pairs = conflicting_heuristics(heuristics)
    conflicting_h_ids = [pair[0] for pair in heuristic_pairs]

    print("Filtered out heuristics:")
    filtered_out_h_ids = set(wrong_direction_h_ids + conflicting_h_ids)
    print(filtered_out_h_ids)
    filtered_heuristics = [h for i, h in enumerate(heuristics) if i not in filtered_out_h_ids]

    print(f"Brute force over all possibilities:")
    nH = len(filtered_heuristics)
    nA = len(ics_a)
    nB = len(ics_b)
    brute_force_result = brute_force_search(
        filtered_heuristics, nA, nB, nH, prove_direction=prove_direction, break_early=args.break_early)

    # print results
    if len(brute_force_result) == 0:
        print("No solution found")
    else:
        for i, result_set in enumerate(brute_force_result):
            print(f"Solution {i+1}:")
            selected_heuristics = result_set
            print("Selected Heuristics:")
            for h in selected_heuristics:
                print(h)
            unmatched_summary, covered_parts_A, covered_parts_B, (ncA, ncB) = format_results(selected_heuristics, ics_a, ics_b)
            print(covered_parts_A)
            print(covered_parts_B)
            print(unmatched_summary)
