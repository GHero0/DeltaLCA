import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import tkinter.messagebox
import customtkinter
import json
import argparse
import os

import sys
sys.path.insert(0, "../sec_6_comparative_impact_assessment") # ugly for now
from compare import ComparativeLCA, Options
from classes import A_MORE, B_MORE, NOT_SURE

customtkinter.set_appearance_mode("Dark")  # Modes: "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self, design_A=None, design_B=None):
        super().__init__()

        # configure window
        self.title("DeltaLCA")
        self.geometry(f"{1600}x{900}")

        # configure grid layout (2x3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure((2, 4), weight=1)
        self.grid_rowconfigure((1, 3), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=120, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="DeltaLCA", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Upload Design A", command=self.sidebar_upload_A_action)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.design_A_fname = customtkinter.CTkLabel(self.sidebar_frame, text="", font=customtkinter.CTkFont(size=10))
        self.design_A_fname.grid(row=2, column=0, padx=10, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Upload Design B", command=self.sidebar_upload_B_action)
        self.sidebar_button_2.grid(row=3, column=0, padx=20, pady=10)
        self.design_B_fname = customtkinter.CTkLabel(self.sidebar_frame, text="", font=customtkinter.CTkFont(size=10))
        self.design_B_fname.grid(row=4, column=0, padx=10, pady=10)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "100%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        # set default values
        self.scaling_optionemenu.set("100%")
        self.appearance_mode_optionemenu.set("Dark")

        # design data
        self.design_A = design_A
        self.design_A_timestamp = None
        self.design_B = design_B
        self.design_B_timestamp = None
        self.design_A_UN = None
        self.design_B_UN = None
        self.design_A_matched = None
        self.design_B_matched = None
        self.compare_backend = None
        self.should_refresh_backend = False
        self.backend_options = Options()
        self.user_added_rules = []

        # initialize table and data if there's any
        self.setup_tables()
        if self.design_A and self.design_B:
            self.design_A_timestamp = os.path.getmtime(self.design_A)
            self.design_B_timestamp = os.path.getmtime(self.design_B)
            self.design_A_fname.configure(text=os.path.basename(self.design_A))
            self.design_B_fname.configure(text=os.path.basename(self.design_B))
            self.update_button_action()

    def load_data_to_table(self):
        # Clear existing data in the tables
        for table in [self.matched_components_table, self.UNmatched_components_table]:
            table.delete(*table.get_children())

        # Insert matched components into the matched_components_table
        nmA = len(self.design_A_matched["IC"])
        nmB = len(self.design_B_matched["IC"])
        itemsA = list(self.design_A_matched["IC"].items())
        itemsB = list(self.design_B_matched["IC"].items())
        for i in range(max(nmA, nmB)):
            name_package_a = f"{itemsA[i][1]['Name']} ({itemsA[i][1]['Package']})" if i < nmA else ""
            name_package_b = f"{itemsB[i][1]['Name']} ({itemsB[i][1]['Package']})" if i < nmB else ""
            self.matched_components_table.insert("", "end", values=(name_package_a, name_package_b))

        # Insert unmatched components into the unmatched_components_table
        nuA = len(self.design_A_UN["IC"])
        nuB = len(self.design_B_UN["IC"])
        itemsA = list(self.design_A_UN["IC"].items())
        itemsB = list(self.design_B_UN["IC"].items())
        for i in range(max(nuA, nuB)):
            name_package_a = f"{itemsA[i][1]['Name']} ({itemsA[i][1]['Package']})" if i < nuA else ""
            name_package_b = f"{itemsB[i][1]['Name']} ({itemsB[i][1]['Package']})" if i < nuB else ""
            self.UNmatched_components_table.insert("", "end", values=(name_package_a, name_package_b))
        
    def load_data_to_ScrollableFrame(self):
        for widget in self.A_scrollable_frame.winfo_children():
            widget.destroy()
        for widget in self.B_scrollable_frame.winfo_children():
            widget.destroy()
        self.A_scrollable_frame_checkBoxes = []
        self.A_scrollable_frame_optionMenus = []
        self.B_scrollable_frame_checkBoxes = []
        self.B_scrollable_frame_optionMenus = []

        # Iterate over the matched components data to create widgets
        i = 0
        for a_ic_name, a_ic_info in self.design_A_UN["IC"].items():
            # Determine the values for CTkOptionMenu based on the component count
            count = a_ic_info["Count"]
            option_menu_values = [str(i) for i in range(count + 1)]  # Generates a list from 0 to count

            # Add CTkOptionMenu on the left with the determined values
            option_menu = customtkinter.CTkOptionMenu(master=self.A_scrollable_frame,
                                                    values=option_menu_values)
            option_menu.grid(row=i, column=0, pady=10, sticky="w")
            self.A_scrollable_frame_optionMenus.append(option_menu)

            # Add CTkCheckBox on the right with the component name
            has_carbonfootprint = "Carbon_Footprint" in a_ic_info and a_ic_info["Carbon_Footprint"] is not None
            checkbox = customtkinter.CTkCheckBox(master=self.A_scrollable_frame, hover_color = "orange", border_color = "orange",
                                                 text=a_ic_info["Name"], text_color="#b2df8a" if has_carbonfootprint else "#ffffff")  # Use the actual component name
            checkbox.grid(row=i, column=1, padx=10, pady=0, sticky="w")
            self.A_scrollable_frame_checkBoxes.append(checkbox)
            i += 1

        for a_ic_name, a_ic_info in self.design_A_matched["IC"].items():
            count = a_ic_info["Count"]
            option_menu_values = [str(i) for i in range(count + 1)]
            option_menu = customtkinter.CTkOptionMenu(master=self.A_scrollable_frame, values=option_menu_values)
            option_menu.grid(row=i, column=0, pady=10, sticky="w")
            self.A_scrollable_frame_optionMenus.append(option_menu)
            has_carbonfootprint = "Carbon_Footprint" in a_ic_info and a_ic_info["Carbon_Footprint"] is not None
            checkbox = customtkinter.CTkCheckBox(master=self.A_scrollable_frame, text=a_ic_info["Name"], text_color="#b2df8a" if has_carbonfootprint else "#ffffff")
            checkbox.grid(row=i, column=1, padx=10, pady=0, sticky="w")
            self.A_scrollable_frame_checkBoxes.append(checkbox)
            i += 1

        j = 0
        for b_ic_name, b_ic_info in self.design_B_UN["IC"].items():
            count = b_ic_info["Count"]
            option_menu_values = [str(i) for i in range(count + 1)]
            option_menu = customtkinter.CTkOptionMenu(master=self.B_scrollable_frame, values=option_menu_values)
            option_menu.grid(row=j, column=0, pady=10, sticky="w")
            self.B_scrollable_frame_optionMenus.append(option_menu)
            has_carbonfootprint = "Carbon_Footprint" in b_ic_info and b_ic_info["Carbon_Footprint"] is not None
            checkbox = customtkinter.CTkCheckBox(master=self.B_scrollable_frame, hover_color = "orange", border_color = "orange",
                                                 text=b_ic_info["Name"], text_color="#b2df8a" if has_carbonfootprint else "#ffffff")
            checkbox.grid(row=j, column=1, padx=10, pady=0, sticky="w")
            self.B_scrollable_frame_checkBoxes.append(checkbox)
            j += 1

        for b_ic_name, b_ic_info in self.design_B_matched["IC"].items():
            count = b_ic_info["Count"]
            option_menu_values = [str(i) for i in range(count + 1)]
            option_menu = customtkinter.CTkOptionMenu(master=self.B_scrollable_frame, values=option_menu_values)
            option_menu.grid(row=j, column=0, pady=10, sticky="w")
            self.B_scrollable_frame_optionMenus.append(option_menu)
            has_carbonfootprint = "Carbon_Footprint" in b_ic_info and b_ic_info["Carbon_Footprint"] is not None
            checkbox = customtkinter.CTkCheckBox(master=self.B_scrollable_frame, text=b_ic_info["Name"], text_color="#b2df8a" if has_carbonfootprint else "#ffffff")
            checkbox.grid(row=j, column=1, padx=10, pady=0, sticky="w")
            self.B_scrollable_frame_checkBoxes.append(checkbox)
            j += 1

    def setup_tables(self):
        # Top Left Table
        # Matched Components Table Title
        self.matched_components_title = customtkinter.CTkLabel(self, text="Matched:", anchor="w", font=("Roboto", 14))
        self.matched_components_title.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))

        # Create and configure the matched components table
        self.matched_components_frame = customtkinter.CTkFrame(self)
        self.matched_components_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.matched_components_table = ttk.Treeview(self.matched_components_frame)
        self.matched_components_table["columns"] = ("Design A", "Design B")
        self.matched_components_table.column("#0", width=0, stretch=tk.NO)
        self.matched_components_table.column("Design A", anchor=tk.CENTER, width=120)
        self.matched_components_table.column("Design B", anchor=tk.CENTER, width=120)
        self.matched_components_table.heading("#0", text="", anchor=tk.CENTER)
        self.matched_components_table.heading("Design A", text="Design A: Device (Package)", anchor=tk.CENTER)
        self.matched_components_table.heading("Design B", text="Design B: Device (Package)", anchor=tk.CENTER)
        self.matched_components_table.grid(row=0, column=0, sticky="nsew")

        # Bottom Left Table
        # Unmatched Components Table Title
        self.UNmatched_components_title = customtkinter.CTkLabel(self, text="Unmatched:", anchor="w", font=("Roboto", 14))
        self.UNmatched_components_title.grid(row=2, column=1, sticky="w", padx=10, pady=(10, 0))
        # Create and configure the UNmatched components table
        self.UNmatched_components_frame = customtkinter.CTkFrame(self)
        self.UNmatched_components_frame.grid(row=3, column=1, sticky="nsew", padx=10, pady=10)
        self.UNmatched_components_table = ttk.Treeview(self.UNmatched_components_frame)
        self.UNmatched_components_table["columns"] = ("Design A", "Design B")
        self.UNmatched_components_table.column("#0", width=0, stretch=tk.NO)
        self.UNmatched_components_table.column("Design A", anchor=tk.CENTER, width=120)
        self.UNmatched_components_table.column("Design B", anchor=tk.CENTER, width=120)
        self.UNmatched_components_table.heading("#0", text="", anchor=tk.CENTER)
        self.UNmatched_components_table.heading("Design A", text="Design A: Device (Package)", anchor=tk.CENTER)
        self.UNmatched_components_table.heading("Design B", text="Design B: Device (Package)", anchor=tk.CENTER)
        self.UNmatched_components_table.grid(row=0, column=0, sticky="nsew")

        # Update Button
        self.update_button = customtkinter.CTkButton(self, text="Update", command=self.update_button_action)
        self.update_button.grid(row=4, column=1, pady=10, padx=10, sticky="ew")

        # Create and configure the comparator option menu
        self.comparator_frame = customtkinter.CTkFrame(self)
        self.comparator_frame.grid(row=1, column=3, sticky="nsew", rowspan=2, padx=10, pady=10)
        # Center the option menu vertically within the frame
        self.comparator_frame.grid_rowconfigure(0, weight=1)
        self.comparator_option_menu = customtkinter.CTkOptionMenu(
            self.comparator_frame, values=[">=", "<="], command=self.comparator_menu_callback)
        self.comparator_option_menu.grid(row=0, column=0, padx=10, pady=(10, 10))
        # Adjust the font size for the option menu values
        self.comparator_option_menu.configure(font=("Roboto", 20))  # Change the font and size as desired

        # Create the CTkScrollableFrame for Design A & B Components
        self.A_scrollable_frame = customtkinter.CTkScrollableFrame(self, label_text="Design A Components")
        self.A_scrollable_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.A_scrollable_frame_optionMenus = []
        self.A_scrollable_frame_checkBoxes = []
        self.B_scrollable_frame = customtkinter.CTkScrollableFrame(self, label_text="Design B Components")
        self.B_scrollable_frame.grid(row=1, column=4, sticky="nsew", padx=10, pady=10)
        self.B_scrollable_frame_optionMenus = []
        self.B_scrollable_frame_checkBoxes = []

        # # Add subtitles for "Quantity" and "Device"
        # subtitle_quantity = tk.Label(self.A_scrollable_frame, text="Quantity", anchor="w")
        # subtitle_quantity.grid(row=0, column=0, sticky="w", padx=10, pady=0)

        # subtitle_device = tk.Label(self.A_scrollable_frame, text="Device", anchor="w")
        # subtitle_device.grid(row=0, column=1, sticky="w", padx=10, pady=0)

        # Add the "ADD" button
        self.add_button = customtkinter.CTkButton(self.comparator_frame, text="Add", command=self.add_rules_event)
        self.add_button.grid(row=1, column=0, pady=10, padx=20, sticky="we")  # Adjust the grid parameters as needed

        # Bottom Right Table
        # Bottom frame for user-added rules
        self.user_added_rules_frame = customtkinter.CTkFrame(self)
        self.user_added_rules_frame.grid(row=3, column=2, columnspan=3, sticky="nsew", padx=10, pady=10)
        self.user_added_rules_table = ttk.Treeview(self.user_added_rules_frame)
        self.user_added_rules_table["columns"] = ("rules")
        self.user_added_rules_table.column("#0", width=0, stretch=tk.NO)
        self.user_added_rules_table.column("rules", anchor=tk.CENTER, width=120)
        self.user_added_rules_table.heading("#0", text="", anchor=tk.CENTER)
        self.user_added_rules_table.heading("rules", text="Manual Rules from User", anchor=tk.CENTER)
        self.user_added_rules_table.grid(row=0, column=0, sticky="nsew")

        # Add the delete button below the user added rules table
        self.delete_rule_button = customtkinter.CTkButton(self.user_added_rules_frame, fg_color = "#6D0000", hover_color = "#430000",
                                                          text="Del", 
                                                          command=self.delete_selected_rule)
        self.delete_rule_button.grid(row=1, column=0, pady=10, padx=10, sticky="we")

        # Configure the frames to expand with the window size
        self.grid_rowconfigure(3, weight=1)
        self.matched_components_frame.grid_rowconfigure(0, weight=1)
        self.matched_components_frame.grid_columnconfigure(0, weight=1)
        self.UNmatched_components_frame.grid_rowconfigure(0, weight=1)
        self.UNmatched_components_frame.grid_columnconfigure(0, weight=1)
        self.user_added_rules_frame.grid_rowconfigure(0, weight=1)
        self.user_added_rules_frame.grid_columnconfigure(0, weight=1)
        self.A_scrollable_frame.grid_rowconfigure(0, weight=1)
        self.A_scrollable_frame.grid_columnconfigure(0, weight=1)
        self.B_scrollable_frame.grid_rowconfigure(0, weight=1)
        self.B_scrollable_frame.grid_columnconfigure(0, weight=1)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def read_json(self, file_path):
        with open(file_path, "r") as file:
            return json.load(file)

    def sidebar_upload_A_action(self):
        print("Upload Design A button click")
        # for now assume the file is the processed inventory json file
        filename = fd.askopenfilename()
        if filename:
            if self.design_A == filename:
                new_timestamp = os.path.getmtime(filename)
                if self.design_A_timestamp != new_timestamp:
                    self.should_refresh_backend = True
                    self.design_A_timestamp = new_timestamp
            else:
                self.design_A = filename
                self.design_A_fname.configure(text=os.path.basename(self.design_A))
                self.should_refresh_backend = True

    def sidebar_upload_B_action(self):
        print("Upload Design B button click")
        # for now assume the file is the processed inventory json file
        filename = fd.askopenfilename()
        if filename:
            if self.design_B == filename:
                new_timestamp = os.path.getmtime(filename)
                if self.design_B_timestamp != new_timestamp:
                    self.should_refresh_backend = True
                    self.design_B_timestamp = new_timestamp
            else:
                self.design_B = filename
                self.design_B_fname.configure(text=os.path.basename(self.design_B))
                self.should_refresh_backend = True

    def update_button_action(self):
        print("Update button click")
        if self.design_A and self.design_B:
            if self.compare_backend is None or self.should_refresh_backend:
                self.compare_backend = ComparativeLCA(self.design_A, self.design_B) #use_v2=False
                self.should_refresh_backend = False
            # gather user rules
            user_rules = []
            for child in self.user_added_rules_table.get_children():
                user_rules.append(self.user_added_rules_table.item(child)["values"])
            self.compare_backend.user_heuristic_rules = user_rules
            print(user_rules)
            self.design_A_matched, self.design_B_matched, self.design_A_UN, self.design_B_UN = self.compare_backend.run(self.backend_options)
            self.load_data_to_ScrollableFrame()
            self.load_data_to_table()

    def comparator_menu_callback(self, comparator):
        curr_prove_direction = A_MORE if comparator == ">=" else B_MORE if comparator == "<=" else NOT_SURE
        if self.backend_options.prove_direction != curr_prove_direction:
            self.backend_options.prove_direction = curr_prove_direction

    def delete_selected_rule(self):
        # Get the selected item
        selected_item = self.user_added_rules_table.selection()

        # Check if an item is actually selected
        if selected_item:
            self.user_added_rules_table.delete(selected_item)
            print(f"Deleted rule: {selected_item}")

    def add_rules_event(self):
        # Initialize an empty list to store the rules
        # Initialize strings to store the rules for both sides of the comparator
        a_side_rules = []
        b_side_rules = []

        # Iterate over the components of Design A
        for a_menu, a_checkbox in zip(self.A_scrollable_frame_optionMenus, self.A_scrollable_frame_checkBoxes):
            # Check if the checkbox is checked and option menu value is >= 1
            if a_checkbox.get() and int(a_menu.get()) >= 1:
                # Format the rule part for Design A and add to the list
                a_side_rule = f"{a_menu.get()} x {a_checkbox.cget('text')}"
                a_side_rules.append(a_side_rule)
                a_checkbox.toggle()
                a_menu.set("0")

        # Iterate over the components of Design B
        for b_menu, b_checkbox in zip(self.B_scrollable_frame_optionMenus, self.B_scrollable_frame_checkBoxes):
            # Check if the checkbox is checked and option menu value is >= 1
            if b_checkbox.get() and int(b_menu.get()) >= 1:
                # Format the rule part for Design B and add to the list
                b_side_rule = f"{b_menu.get()} x {b_checkbox.cget('text')}"
                b_side_rules.append(b_side_rule)
                b_checkbox.toggle()
                b_menu.set("0")

        # Combine the rules from both sides with the comparator in between
        if a_side_rules and b_side_rules:
            # Get the value of the comparator
            comparator = self.comparator_option_menu.get()
            # Format the full rule string
            full_rule = f"{' + '.join(a_side_rules)} {comparator} {' + '.join(b_side_rules)}"
            # Insert the full rule into the user added rules table
            self.user_added_rules_table.insert("", "end", values=(full_rule,))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="UI for Comparative LCA")
    parser.add_argument("--example_folder", type=str, default="../sec_6_comparative_impact_assessment/toy_examples")
    parser.add_argument("--design_A", type=str, default="Arduino_Leonardo_Rev3d.json")
    parser.add_argument("--design_B", type=str, default="Arduino_MKR_Fox_1200.json")
    args = parser.parse_args()

    app = App(design_A=os.path.join(args.example_folder, args.design_A), design_B=os.path.join(args.example_folder, args.design_B))
    app.mainloop()
