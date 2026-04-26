import os, json, re, sys


def get_design_config(design_name):
    """Get design configuration (top module, clock, reset) from design_all.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "design_all.json")
    with open(config_path, 'r') as f:
        design_dict = json.load(f)
    if design_name not in design_dict:
        raise ValueError(f"Design '{design_name}' not found in design_all.json")
    info = design_dict[design_name]
    return {
        "top": info[0],
        "clk": info[1],
        "rst": info[2],
        "tpe": info[3],
    }


def bit_2_word(reg_name):
    """Convert bit-level register name to word-level"""
    reg_re1 = re.findall(r'_reg\[(\d)*\]\[(\d)*\]$', reg_name)
    if reg_re1:
        reg_name = re.sub(r'_reg\[(\d)*\]\[(\d)*\]$', r'', reg_name)
    reg_re2 = re.findall(r'_reg\[(\d)*\]$', reg_name)
    if reg_re2:
        reg_name = re.sub(r'_reg\[(\d)*\]$', r'', reg_name)
    reg_re3 = re.findall(r'_reg$', reg_name)
    if reg_re3:
        reg_name = re.sub(r'_reg$', r'', reg_name)
    reg_re4 = re.findall(r'\[(\d)*\]$', reg_name)
    if reg_re4:
        reg_name = re.sub(r'\[(\d)*\]$', r'', reg_name)
    return reg_name


def run_syn(design_name, design_version):
    """
    Run Synopsys Design Compiler synthesis.
    Generates gate-level netlist from RTL.
    """
    config = get_design_config(design_name)
    design_top = config["top"]
    design_clk = config["clk"]
    design_tpe = config["tpe"]

    print(f"=== Running Synthesis ===")
    print(f"Design: {design_name}.{design_version}")
    print(f"Top module: {design_top}")
    print(f"Clock: {design_clk}")

    # Generate synthesis TCL script from template
    tmp_path = "./scr/syn.tcl"
    with open(tmp_path, 'r') as f:
        syn_tcl = f.readlines()

    tcl_file = f"./syn_{design_name}.{design_version}.tcl"
    with open(tcl_file, 'w') as f:
        for line in syn_tcl:
            line = line.replace("design_name_here", f"{design_name}.{design_version}")
            line = line.replace("design_top_here", f"{design_top}")
            line = line.replace("design_clk_here", f"{design_clk}")
            line = line.replace("design_version_here", f"{design_version}")
            line = line.replace("design_tpe_here", f"{design_tpe}")
            f.writelines(line)

    # Create output directories
    os.makedirs(f"./log", exist_ok=True)
    os.makedirs(f"./reports/{design_name}.{design_version}", exist_ok=True)
    os.makedirs(f"./netlist", exist_ok=True)
    os.makedirs(f"./output/{design_name}.{design_version}", exist_ok=True)

    # Run dc_shell
    log_file = f"./log/syn_{design_name}.{design_version}.log"
    syn_cmd = f"dc_shell -f {tcl_file} > {log_file}"
    ret = os.system(syn_cmd)

    # Cleanup
    os.system(f"rm -f {tcl_file}")

    print(f"=== Synthesis Complete ===")
    return ret == 0


def run_lec(design_name, design_version):
    """
    Run Synopsys Formality for equivalence checking.
    Verifies synthesized netlist matches RTL.
    """
    config = get_design_config(design_name)
    design_top = config["top"]

    print(f"=== Running Formality (LEC) ===")
    print(f"Design: {design_name}.{design_version}")
    print(f"Top module: {design_top}")

    # Generate FM TCL script from template
    tmp_path = "./scr/fm.tcl"
    with open(tmp_path, 'r') as f:
        fm_tcl = f.readlines()

    tcl_file = f"./fm_{design_name}.{design_version}.tcl"
    with open(tcl_file, 'w') as f:
        for line in fm_tcl:
            line = line.replace("design_name_here", f"{design_name}")
            line = line.replace("design_name_new_here", f"{design_name}.{design_version}")
            line = line.replace("design_top_here", f"{design_top}")
            f.writelines(line)

    # Create log directory
    os.makedirs(f"./log", exist_ok=True)
    os.makedirs(f"./output/{design_name}.{design_version}", exist_ok=True)

    # Run fm_shell
    log_file = f"./log/lec_{design_name}.{design_version}.log"
    fm_cmd = f"fm_shell -f {tcl_file} > {log_file}"
    ret = os.system(fm_cmd)

    # Cleanup
    os.system(f"rm -f {tcl_file}")

    # Parse and save LEC result
    lec_result = parse_LEC_report(design_name, design_version)
    with open(f"./output/{design_name}.{design_version}/LEC_result.txt", 'w') as f:
        f.write(f"LEC: {lec_result}\n")

    print(f"=== LEC Complete: {'PASSED' if lec_result else 'FAILED'} ===")
    return lec_result


def run_sim(design_name, design_version):
    rtl_path = f"./rtl/{design_name}.{design_version}.v"
    tb_path = f"./tb/{design_name}.v"
    log_file = f"./log/sim_{design_name}.{design_version}.log"
    vcs_cmd = f"vcs -sverilog +v2k -timescale=1ns/1ns       \
		-debug_all         							\
		-l compile.log 								\
		{rtl_path} {tb_path} > {log_file}"
    sim_cmd = f"./simv -l run.log >> {log_file}"
    os.system(vcs_cmd)
    os.system(sim_cmd)


def run_sec(design_name, design_version):
    """
    Run Cadence Jasper SEC.
    Check the equivalence between the original RTL and optimized RTL.
    """
    config = get_design_config(design_name)
    design_top = config["top"]
    design_clk = config["clk"]
    design_rst = config["rst"]
    design_tpe = config["tpe"]
    if design_rst == "":
        design_rst = "None"
        print("Warning: No reset signal defined for SEC")
        exit()

    print(f"=== Running SEC ===")
    if os.path.exists(f"./jgproject"):
        os.system(f"rm -rf ./jgproject")
    # Generate synthesis TCL script from template
    tmp_path = "./scr/sec.tcl"
    with open(tmp_path, 'r') as f:
        syn_tcl = f.readlines()

    tcl_file = f"./sec_{design_name}.{design_version}.tcl"
    with open(tcl_file, 'w') as f:
        for line in syn_tcl:
            line = line.replace("design_name_golden_here", f"{design_name}.v0")
            line = line.replace("design_name_here", f"{design_name}.{design_version}")
            line = line.replace("design_top_here", f"{design_top}")
            line = line.replace("design_clk_here", f"{design_clk}")
            line = line.replace("design_rst_here", f"{design_rst}")
            line = line.replace("design_tpe_here", f"{design_tpe}")
            f.writelines(line)

    # Create output directories
    os.makedirs(f"./log", exist_ok=True)

    # Run dc_shell
    log_file = f"./log/sec_{design_name}.{design_version}.log"
    syn_cmd = f"jaspergold -sec -batch -tcl {tcl_file} > {log_file}"
    # syn_cmd = f"jaspergold -sec -batch -tcl {tcl_file}"
    ret = os.system(syn_cmd)

    # Cleanup
    os.system(f"rm -f {tcl_file}")

    print(f"=== SEC Complete ===")
    return ret == 0




def parse_LEC_report(design_name, design_version):
    """Parse Formality log to determine pass/fail"""
    lec_rpt_path = f"./log/lec_{design_name}.{design_version}.log"
    try:
        with open(lec_rpt_path, 'r') as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            if "Verification Results" in line:
                result_line = lines[idx + 1]
                if "SUCCEEDED" in result_line:
                    return True
        return False
    except FileNotFoundError:
        print(f"Warning: LEC log not found: {lec_rpt_path}")
        return False
    

def parse_sim_report(design_name, design_version):
    """Parse simulation log to extract results (placeholder)"""
    sim_rpt_path = f"./log/sim_{design_name}.{design_version}.log"
    ret = False
    with open(sim_rpt_path, 'r') as f:
        lines = f.readlines()
    # Placeholder parsing logic
    for line in lines:
        if "PASS" in line:
            ret = True

    with open(f"./output/{design_name}.{design_version}/SEC_result.txt", 'w') as f:
        f.write(f"{'PASSED' if ret else 'FAILED'}\n")
    print(f"SEC result: {'PASSED' if ret else 'FAILED'}")


def parse_sec_report(design_name, design_version):
    """Parse SEC log to determine pass/fail"""
    sec_rpt_path = f"./log/sec_{design_name}.{design_version}.log"
    ret = False
    with open(sec_rpt_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        proven_line = re.findall(r"^proven$", line)
        if proven_line:
            ret = True
            break
    with open(f"./output/{design_name}.{design_version}/SEC_result.txt", 'w') as f:
        f.write(f"{'PASSED' if ret else 'FAILED'}\n")
    print(f"SEC result: {'PASSED' if ret else 'FAILED'}")


def parse_timing_report(design_name, design_version):
    """Parse timing report and extract critical paths"""
    timing_rpt_path = f"./reports/{design_name}.{design_version}/timing.rpt"
    timing_dict_bit, timing_dict_word = {}, {}

    try:
        with open(timing_rpt_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Warning: Timing report not found: {timing_rpt_path}")
        return

    start_lst, end_lst, slack_lst = [], [], []
    start_word_lst, end_word_lst = [], []

    for line in lines:
        slack_re = re.findall(r"slack \(.*\)(\s+)(\S+)", line)
        if "Startpoint:" in line:
            start = line.split("Startpoint:")[1].split()[0]
            start_lst.append(start)
            start_word_lst.append(bit_2_word(start))
        if "Endpoint:" in line:
            end = line.split("Endpoint:")[1].split()[0]
            end_lst.append(end)
            end_word_lst.append(bit_2_word(end))
        if slack_re:
            slack = slack_re[0][1].strip()
            slack_lst.append(float(slack))

    if not (len(start_lst) == len(end_lst) == len(slack_lst)):
        print("Warning: Timing report parsing error - mismatched lengths")
        return

    for i in range(len(start_lst)):
        timing_dict_bit[f"{start_lst[i]} -> {end_lst[i]}"] = slack_lst[i]

    for i in range(len(start_word_lst)):
        key = f"{start_word_lst[i]} -> {end_word_lst[i]}"
        if key not in timing_dict_word or slack_lst[i] < timing_dict_word[key]:
            timing_dict_word[key] = slack_lst[i]

    output_dir = f"./output/{design_name}.{design_version}"
    os.makedirs(output_dir, exist_ok=True)

    # with open(f"{output_dir}/timing_bit.json", 'w') as f:
    #     json.dump(timing_dict_bit, f, indent=4)
    with open(f"{output_dir}/timing_word.json", 'w') as f:
        json.dump(timing_dict_word, f, indent=4)

    print(f"Timing report parsed: {len(timing_dict_bit)} paths")


def parse_PPA_report(design_name, design_version):
    """Parse QoR and power reports to extract PPA metrics"""
    ppa_rpt_dir = f"./reports/{design_name}.{design_version}/"

    area, wns, tns, pwr = None, None, None, None

    # Parse QoR report
    qor_rpt_path = f"{ppa_rpt_dir}/qor.rpt"
    try:
        with open(qor_rpt_path, 'r') as f:
            for line in f:
                if "  Design Area:" in line:
                    area = float(line.split(":")[1].strip())
                if "Critical Path Slack:" in line:
                    if wns is not None:
                        continue
                    wns = float(line.split(":")[1].strip())
                if "Total Negative Slack:" in line:
                    if tns is not None:
                        continue
                    tns = float(line.split(":")[1].strip())
    except FileNotFoundError:
        print(f"Warning: QoR report not found: {qor_rpt_path}")

    # Parse power report
    pwr_rpt_path = f"{ppa_rpt_dir}/power.rpt"
    try:
        with open(pwr_rpt_path, 'r') as f:
            for line in f:
                if "Total Dynamic Power    = " in line:
                    pwr = float(line.split("=")[1].strip().split()[0])
    except FileNotFoundError:
        print(f"Warning: Power report not found: {pwr_rpt_path}")

    ppa_dct = {
        "Area": area,
        "WNS": wns,
        "TNS": tns,
        "Power": pwr
    }

    output_dir = f"./output/{design_name}.{design_version}"
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/PPA_report.json", 'w') as f:
        json.dump(ppa_dct, f, indent=4)

    print(f"Design: {design_name}, Area: {area}, WNS: {wns}, TNS: {tns}, Power: {pwr}")
    return ppa_dct


def get_report_sec(design_name, design_version):
    """Parse all reports and generate output JSON files"""
    print(f"=== Generating Reports for {design_name}.{design_version} ===")

    os.makedirs(f"./output/{design_name}.{design_version}", exist_ok=True)

    # Parse all reports
    parse_PPA_report(design_name, design_version)
    parse_timing_report(design_name, design_version)

    # LEC result should already exist from run_lec, but check anyway

    # lec_file = f"./output/{design_name}.{design_version}/LEC_result.txt"
    # if not os.path.exists(lec_file):
    #     lec_result = parse_LEC_report(design_name, design_version)
    #     with open(lec_file, 'w') as f:
    #         f.write(f"LEC: {lec_result}\n")
    # parse_sim_report(design_name, design_version)

    parse_sec_report(design_name, design_version)
    print(f"=== Reports saved to ./output/{design_name}.{design_version}/ ===")


def get_report_sim(design_name, design_version):
    """Parse all reports and generate output JSON files"""
    print(f"=== Generating Reports for {design_name}.{design_version} ===")

    os.makedirs(f"./output/{design_name}.{design_version}", exist_ok=True)

    # Parse all reports
    parse_PPA_report(design_name, design_version)
    parse_timing_report(design_name, design_version)
    parse_sim_report(design_name, design_version)
    print(f"=== Reports saved to ./output/{design_name}.{design_version}/ ===")


def run_design(design_name, design_version):
    """
    Run full synthesis flow:
    1. Run synthesis (dc_shell)
    2. Run LEC (fm_shell)
    3. Parse and save reports
    """

    run_syn(design_name, design_version)

    # run_lec(design_name, design_version)
    # run_sim(design_name, design_version)

    if design_name in ['LSTM']:
        run_sim(design_name, design_version)
        get_report_sim(design_name, design_version)
    else:

        run_sec(design_name, design_version)
        get_report_sec(design_name, design_version)


def print_usage():
    print("""Usage: python run_design.py <design_name> <design_version>
Examples:
  python run_design.py tv80 v0           # Full flow
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    design_name = sys.argv[1]
    design_version = sys.argv[2]

    run_design(design_name, design_version)

