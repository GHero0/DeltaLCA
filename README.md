# DeltaLCA: Comparative Life-Cycle Assessment for Electronics Design
Zhihan Zhang*, Felix Hähnlein*, Yuxuan Mei*, Zachary Englhardt, Shwetak Patel, Adriana Schulz, Vikram Iyer

## Abstract
Reducing the environmental footprint of electronics and computing devices requires new tools that empower designers to make informed decisions about sustainability during the design process itself. This is not possible with current tools for life cycle assessment (LCA) which require substantial domain expertise and time to evaluate the numerous chips and other components that make up a device. We observe first that informed decision-making does not require absolute metrics and can instead be done by comparing designs. Second, we can use domain-specific heuristics to perform these comparisons. We combine these insights to develop DeltaLCA, an open-source interactive design tool that addresses the dual challenges of automating life cycle inventory generation and data availability by performing comparative analyses of electronics designs. Users can upload standard design files from Electronic Design Automation (EDA) software and the tool will guide them through determining which one has greater carbon footprints. DeltaLCA leverages electronics-specific LCA datasets and heuristics and tries to automatically rank the two designs, prompting users to provide additional information only when necessary. We show through case studies DeltaLCA achieves the same result as evaluating full LCAs, and that it accelerates LCA comparisons from eight expert-hours to a single click for devices with ~30 components, and 15 minutes for more complex devices with ~100 components.

---

For more information, read the full paper, which was directly accepted with all reviewers recommending "Acceptable with minor (or no) changes", published in [IMWUT 2024](https://dl.acm.org/doi/abs/10.1145/3643561).

## System Overview
DeltaLCA enables designers to rapidly compare the environmental impact (EI) of two PCB designs. In the traditional Life Cycle Assessment (LCA) pipeline (top row), LCA experts manually generate an inventory of parts and match them to a database to calculate the EI. DeltaLCA (bottom row) first automates inventory generation and estimates partial EI for known components, then performs a user-in-the-loop comparison using domain-specific heuristics to determine if Design A has a greater EI than Design B.

![DeltaLCA](/figures/system_overview.png)

Our automated LCI pipeline starts by parsing the PCB design files from common design software into a parts list, then infers core specifications such as die sizes using online resources, and finally generates the partial inventory with partial EIs based on publicly available data.

![auto_inventory_pipeline](/figures/auto_inventory_pipeline.png)

## User-in-the-Loop
Our comparison algorithm uses parts either for pairwise comparisons (grey nodes) via heuristics (edges) or for carbon footprint comparison (green nodes). (1) The initial comparison results are first delivered to the user. (2) Drawing from the user's domain knowledge, the user adds comparison rules using any parts available to solve the unmatched parts (orange nodes). (3) The results can be updated, taking into account the user-defined rules.

<img src="/figures/user_in_the_loop.png" style="width: 50%;" alt="user in the loop">


## Getting Started

Following user feedback, we've recognized that the comparative LCA methodology has broader applications beyond PCB designs. Therefore, we've separated the codebase to allow independent execution of different components.

### Key Components

1. **Life Cycle Inventory Generation** (`sec_5_life_cycle_inventory/notebook.ipynb`):
   - A step-by-step notebook corresponding to [Section 5 of our paper](https://dl.acm.org/doi/pdf/10.1145/3643561)
   - Demonstrates how to generate a partial life cycle inventory from raw EAGLE PCB board layout (.brd) files

2. **Comparative Impact Assessment** (`sec_6_comparative_impact_assessment`):
   - Contains all code for [Section 6 of our paper](https://dl.acm.org/doi/pdf/10.1145/3643561)
   - Implements comparison techniques based on domain-specific heuristics (`sec_6_comparative_impact_assessment\heuristics.py`)
   - Includes a user interface (`user_interface/UI.py`) for quick comparison testing
   - Provides three toy examples under `sec_6_comparative_impact_assessment/toy_examples` that can be used with the UI to test comparisons directly

### Prerequisites

- Install Python 3.8 or higher
- Get a free API Key at [Digikey](https://developer.digikey.com/) if you want to run the corresponding code cell in `sec_5_life_cycle_inventory/notebook.ipynb`. For more information on using the API in Python, check the [Digikey API documentation](https://github.com/peeter123/digikey-api)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/iamZhihanZhang/DeltaLCA
   ```
2. Install Python packages
   ```sh
   pip install -r requirements.txt
   ```

## Cite DeltaLCA
```
@article{10.1145/3643561,
author = {Zhang, Zhihan and H\"{a}hnlein, Felix and Mei, Yuxuan and Englhardt, Zachary and Patel, Shwetak and Schulz, Adriana and Iyer, Vikram},
title = {DeltaLCA: Comparative Life-Cycle Assessment for Electronics Design},
year = {2024},
issue_date = {March 2024},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
volume = {8},
number = {1},
url = {https://doi.org/10.1145/3643561},
doi = {10.1145/3643561},
journal = {Proc. ACM Interact. Mob. Wearable Ubiquitous Technol.},
month = mar,
articleno = {29},
numpages = {29},
keywords = {Domain-Specific Heuristics, Life Cycle Assessment, Linear Programming, Sustainable Computing}
}
```