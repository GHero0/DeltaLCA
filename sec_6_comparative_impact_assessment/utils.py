import json
from classes import *
from precompute_carbon_number import get_nonIC_carbon_footprint

def parse_non_ics(json_data, ic_count):
    # create a dummy IC component for all the non-IC components
    board_footprint, non_IC_footprint = get_nonIC_carbon_footprint(json_data)
    board_json = {
            "Name": "Board",
            "Package": f"CO2={board_footprint:.4f}",
            "Carbon_Footprint": board_footprint,
            "Count": 1
        }
    non_IC_json = {
            "Name": "Non_ICs",
            "Package": f"CO2={non_IC_footprint:.4f}",
            "Carbon_Footprint": non_IC_footprint,
            "Count": 1
        }
    return [IC(board_json, ic_count), IC(non_IC_json, ic_count + 1)]

def parse_non_ics2(json_data, ic_count):
    # create a dummy IC component for all the non-IC components
    board_footprint, non_IC_footprint = get_nonIC_carbon_footprint(json_data)
    non_IC_json = {
            "Name": "Board_and_non_ICs",
            "Package": f"CO2={non_IC_footprint:.4f}",
            "Carbon_Footprint": board_footprint + non_IC_footprint,
            "Count": 1
        }
    return [IC(non_IC_json, ic_count)]

def load_design(fpath, verbose=False):
    print("Load design from", fpath)
    with open(fpath, "r") as f:
        json_data = json.load(f)
    if verbose:
        print(json_data)
    ic_json_data = json_data["IC"].values()
    ncount = 0
    ics = []
    for dict_design in ic_json_data:
        count = int(dict_design["Count"])
        for j in range(count):
            ics.append(IC(dict_design, ncount + j))
        ncount += count
    json_data.pop("IC")
    non_ics = parse_non_ics(json_data, ncount)
    return ics + non_ics

def format_results(selected_heuristics, selected_footprints_a, selected_footprints_b, ics_a, ics_b):
    unmatched_summary = "Unmatched ICs from design A:\n"
    covered_parts_A = "Covered parts A:\n"
    covered_a_ids = set([aid for h in selected_heuristics for aid in h.parts_a]+selected_footprints_a)
    for ic_a in ics_a:
        if ic_a.id not in covered_a_ids:
            unmatched_summary += f"    {ic_a}\n"
        else:
            covered_parts_A += f"    {ic_a}\n"
    unmatched_summary += "Unmatched ICs from design B:\n"
    covered_parts_B = "Covered parts B:\n"
    covered_b_ids = set([bid for h in selected_heuristics for bid in h.parts_b]+selected_footprints_b)
    for ic_b in ics_b:
        if ic_b.id not in covered_b_ids:
            unmatched_summary += f"    {ic_b}\n"
        else:
            covered_parts_B += f"    {ic_b}\n"
    return unmatched_summary, covered_parts_A, covered_parts_B, (len(covered_a_ids), len(covered_b_ids))

def format_results_to_json(selected_heuristics, selected_footprints_a, selected_footprints_b, ics_a, ics_b):
    matched_A, matched_B, UNmatched_A, UNmatched_B = {}, {}, {}, {}
    covered_a_ids = [aid for h in selected_heuristics for aid in h.parts_a]+selected_footprints_a
    for ic_a in ics_a:
        if ic_a.id not in covered_a_ids:
            if ic_a.Name not in UNmatched_A:
                UNmatched_A[ic_a.Name] = ic_a.jsondata.copy()
            else:
                UNmatched_A[ic_a.Name]["Count"] += 1
    for covered_a_id in covered_a_ids:
        for ic_a in ics_a:
            if covered_a_id == ic_a.id:
                if ic_a.Name not in matched_A:
                    matched_A[ic_a.Name] = ic_a.jsondata.copy()
                else:
                    matched_A[ic_a.Name]["Count"] += 1
                break
    covered_b_ids = [bid for h in selected_heuristics for bid in h.parts_b]+selected_footprints_b
    covered_b_ids_set = set(covered_b_ids)
    for ic_b in ics_b:
        if ic_b.id not in covered_b_ids_set:
            if ic_b.Name not in UNmatched_B:
                UNmatched_B[ic_b.Name] = ic_b.jsondata.copy()
            else:
                UNmatched_B[ic_b.Name]["Count"] += 1
    track_set = set()
    for covered_b_id in covered_b_ids:
        if covered_b_id in track_set:
            continue
        track_set.add(covered_b_id)
        for ic_b in ics_b:
            if covered_b_id == ic_b.id:
                if ic_b.Name not in matched_B:
                    matched_B[ic_b.Name] = ic_b.jsondata.copy()
                else:
                    matched_B[ic_b.Name]["Count"] += 1
    return {"IC": matched_A}, {"IC": matched_B}, {"IC": UNmatched_A}, {"IC": UNmatched_B}
