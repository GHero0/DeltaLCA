import numpy as np
from time import perf_counter_ns

from heuristics import heuristic_functions, heuristic_functions_v2
from classes import *
from utils import load_design, format_results_to_json
from ortools_model import select_heuristics

class Options:
    def __init__(self, prove_direction=A_MORE, use_carbon_footprint=True):
        self.prove_direction = prove_direction
        self.use_carbon_footprint = use_carbon_footprint

class ComparativeLCA:
    def __init__(self, design_A_fpath, design_B_fpath, use_v2=False):
        self.design_A = load_design(design_A_fpath)
        self.design_B = load_design(design_B_fpath)
        self.h_functions = heuristic_functions_v2 if use_v2 else heuristic_functions
        self.user_heuristic_rules = [] # to be modified from the UI
        self.user_rules_map = {} # to be modified from the UI

    def run(self, options):
        # precomputation
        start_time = perf_counter_ns()
        heuristics = []
        for ic_a in self.design_A:
            for ic_b in self.design_B:
                for h in self.h_functions:
                    heuristics.append(Heuristic(ic_a, ic_b, h))
        end_time = perf_counter_ns()
        print(f"Precomputation time: {(end_time - start_time)*1e-6:.4f} milliseconds")

        # process user heuristic rules
        start_time = perf_counter_ns()
        comparator_symbol = ">=" if options.prove_direction == A_MORE else "<=" if options.prove_direction == B_MORE else ""
        # Making the heuristic rule ids unique
        left_user_used_ids = []
        for rule in self.user_heuristic_rules:
            if rule[0] in self.user_rules_map:
                left_user_used_ids += [aid for h in self.user_rules_map[rule[0]] for aid in h.parts_a]
        left_user_used_ids = set(left_user_used_ids)
        for rule in self.user_heuristic_rules:
            if rule[0] in self.user_rules_map:
                continue
            # rule is a list of values, in this case the table only has one column so 0th item is the string itself
            lefthandside, righthandside = rule[0].split(comparator_symbol)
            lefthandside = lefthandside.strip().split(" + ")
            left_components_list = []
            total_left_count = 0
            for left in lefthandside:
                count_str, name = left.strip().split(" x ")
                count = int(count_str)
                total_left_count += count
            left_used = set()
            while True:
                has_count_0 = False
                left_components = [] # one set
                for left in lefthandside:
                    count_str, name = left.strip().split(" x ")
                    count = int(count_str)
                    for ic_a in self.design_A:
                        if ic_a.Name == name and ic_a.id not in left_used and ic_a.id not in left_user_used_ids:
                            left_components.append(ic_a)
                            left_used.add(ic_a.id)
                            count -= 1
                            if count == 0:
                                has_count_0 = True
                                break
                if len(left_components) == total_left_count:
                    left_components_list.append(left_components)
                    left_components = []
                if has_count_0:
                    break
            righthandside = righthandside.strip().split(" + ")
            right_components_list = []
            total_right_count = 0
            for right in righthandside:
                count_str, name = right.strip().split(" x ")
                count = int(count_str)
                total_right_count += count
            right_used = set()
            while True:
                has_count_0 = False
                right_components = [] # one set
                for right in righthandside:
                    count_str, name = right.strip().split(" x ")
                    count = int(count_str)
                    for ic_b in self.design_B:
                        if ic_b.Name == name and ic_b.id not in right_used:
                            right_components.append(ic_b)
                            right_used.add(ic_b.id)
                            count -= 1
                            if count == 0:
                                has_count_0 = True
                                break
                if len(right_components) == total_right_count:
                    right_components_list.append(right_components)
                    right_components = []
                if has_count_0:
                    break
            # apply rules as many times as we could
            mapped_heuristics = []
            for num_applied in range(min(len(left_components_list), len(right_components_list))):
                left_components = left_components_list[num_applied]
                right_components = right_components_list[num_applied]
                mapped_heuristics.append(Heuristic(
                    left_components, right_components, lambda IC_A, IC_B: (options.prove_direction, f"User defined rule: {rule[0]}"), is_user_defined=True))
                print(mapped_heuristics[-1])
            self.user_rules_map[rule[0]] = mapped_heuristics
        rule_text = [rule[0] for rule in self.user_heuristic_rules]
        for rule, mapped_heuristics in self.user_rules_map.items():
            if rule in rule_text:
                heuristics += mapped_heuristics
        end_time = perf_counter_ns()
        print(f"User rule parsing time: {(end_time - start_time)*1e-6:.4f} milliseconds")

        # select heuristics
        a_indices = [ic_a.id for ic_a in self.design_A]
        b_indices = [ic_b.id for ic_b in self.design_B]
        footprints_a = [ic_a.Carbon_Footprint for ic_a in self.design_A]
        footprints_b = [ic_b.Carbon_Footprint for ic_b in self.design_B]
        start_time = perf_counter_ns()
        selected_heuristics, selected_footprints_a, selected_footprints_b = select_heuristics(
            heuristics, filter_out_conflicts=True, prove_direction=options.prove_direction, use_carbon_footprint=options.use_carbon_footprint,
            a_indices=a_indices, b_indices=b_indices, footprints_a=footprints_a, footprints_b=footprints_b)
        end_time = perf_counter_ns()
        print(f"Comparison algorithm time: {(end_time - start_time)*1e-6:.4f} milliseconds")

        # print results
        print("Selected Heuristics:")
        for h in selected_heuristics:
            print(h)
        if options.use_carbon_footprint:
            print("Carbon footprint selection")
            print("Carbon footprint A:", np.sum([footprints_a[i] for i in selected_footprints_a]))
            print("Carbon footprint B:", np.sum([footprints_b[i] for i in selected_footprints_b]))
            print("Footprint selected parts A:", selected_footprints_a)
            print("Footprint selected parts B:", selected_footprints_b)

        return format_results_to_json(selected_heuristics, selected_footprints_a, selected_footprints_b, self.design_A, self.design_B)
