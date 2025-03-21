import os
import argparse

from heuristics import heuristic_functions, heuristic_functions_v2
from classes import *
from utils import *
from ortools_model import conflicting_heuristics
from bruteforce_model import verify_proposition

def covered_from_parts(current_selection, prove_direction):
    if prove_direction == A_MORE:
        return [p for h in current_selection for p in h.parts_a]
    elif prove_direction == B_MORE:
        return [p for h in current_selection for p in h.parts_b]
    else:
        raise Exception("ERROR: invalid prove_direction")

def can_add_heuristic(h_add, current_selection, prove_direction=A_MORE):
    if len(current_selection) == 0:
        return 0
    if prove_direction == A_MORE:
        from_parts = covered_from_parts(current_selection, prove_direction) + h_add.parts_a
        unique_from_parts = set(from_parts)
        # check that from parts are not used more than once
        if len(unique_from_parts) != len(from_parts):
            return -1
        to_parts = set([p for h in current_selection for p in h.parts_b] + h_add.parts_b)
        return len(unique_from_parts) + len(to_parts)
    elif prove_direction == B_MORE:
        from_parts = covered_from_parts(current_selection, prove_direction) + h_add.parts_b
        unique_from_parts = set(from_parts)
        if len(unique_from_parts) != len(from_parts):
            return -1
        to_parts = set([p for h in current_selection for p in h.parts_a] + h_add.parts_a)
        return len(unique_from_parts) + len(to_parts)

def greedy_search(heuristics, nA, nB, prove_direction=A_MORE, randomize=True):
    greedy_result = None
    if len(heuristics) == 0:
        return greedy_result
    if randomize:
        import random
        random.shuffle(heuristics)
    print(f"Greedy search with initial heuristic: {heuristics[0]}")
    current_selection = [heuristics[0]]
    remaining_heuristics = heuristics[1:]
    while True:
        best_score = -1
        best_heuristic = None
        for h in remaining_heuristics:
            score = can_add_heuristic(h, current_selection)
            if score > best_score:
                best_score = score
                best_heuristic = h
        if best_score == -1:
            break
        current_selection.append(best_heuristic)
        remaining_heuristics.remove(best_heuristic)
        if verify_proposition(current_selection, nA, nB, prove_direction):
            greedy_result = current_selection
            break
    return greedy_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Greedy search for LCA-for-PCB')
    parser.add_argument('--example_folder', type=str, default="Arduino_PCB_design_files")
    parser.add_argument('--design_A', type=str, default="PCB_summary_Leonardo_Rev3d.json")
    parser.add_argument('--design_B', type=str, default="PCB_summary_MKR1200.json")
    parser.add_argument('--prove_direction', type=str, default="A_MORE")
    parser.add_argument('--use_v2', action='store_true', default=False)
    parser.add_argument('--should_randomize', action='store_true', default=False)
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

    print(f"Greedily select heuristics to prove the direction {args.prove_direction}:")
    nA = len(ics_a)
    nB = len(ics_b)
    greedy_result = greedy_search(filtered_heuristics, nA, nB, prove_direction=prove_direction, randomize=args.should_randomize)

    # print results
    if greedy_result is None:
        print("Greedy search failed to find a solution.")
    else:
        selected_heuristics = greedy_result
        print("Selected Heuristics:")
        for h in selected_heuristics:
            print(h)
        unmatched_summary, covered_parts_A, covered_parts_B, (ncA, ncB) = format_results(selected_heuristics, ics_a, ics_b)
        print(covered_parts_A)
        print(covered_parts_B)
        print(unmatched_summary)
