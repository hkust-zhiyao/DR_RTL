# ==================================================
# TCL Script for Logic Synthesis using Synopsys DC
# ==================================================

set tool "DC"
set hdlin_enable_designware_support true
# Set the design environment
set search_path [list ./lib ./input]
set target_library [list "nangate.db"]
set link_library [concat "*" $target_library]

# Define the top-level module name
set DESIGN_NAME "design_name_here"
set TOP_NAME "design_top_here"

file mkdir ./work/${DESIGN_NAME}
define_design_lib WORK -path ./work/${DESIGN_NAME}
# Read the design files
# read_verilog ./rtl/${DESIGN_NAME}/*.v
set rtl_path ./rtl/${DESIGN_NAME}.design_tpe_here
# set filelist ./filelist/list_${DESIGN_NAME}.f
analyze -format design_tpe_hereerilog -recursive -autoread $rtl_path -top ${TOP_NAME}

# Elaborate the design
elaborate $TOP_NAME

# Set design constraints
create_clock -name design_clk_here -period 0.1 [get_ports design_clk_here]
# set_input_delay 1 [get_ports {in1 in2 in3}] -clock clk
# set_output_delay 1 [get_ports {out1 out2}] -clock clk
set_max_delay -to [all_outputs] -from [all_inputs] 0.1

# # Set drive strength and load
# set_drive 0.1 [get_ports {in1 in2 in3}]
# set_load 0.1 [get_ports {out1 out2}]

# # Optimization constraints
# set_max_area 0  ;# No area constraint (optimize for timing)
# set_max_transition 0.2 [get_ports clk]
# set_max_fanout 10 [get_ports {in1 in2 in3}]

# Run synthesis
# compile_ultra
compile
# compile -map_effort medium -incremental_mapping

# 7. Write out the synthesized netlist with hierarchy
ungroup -all -flatten

# Report results
## create folders for reports and netlist
file mkdir reports/${DESIGN_NAME}
report_timing -tran -net -input -max_paths 100000 > reports/${DESIGN_NAME}/timing.rpt
report_area > reports/${DESIGN_NAME}/area.rpt
report_power > reports/${DESIGN_NAME}/power.rpt
report_qor > reports/${DESIGN_NAME}/qor.rpt

# Save synthesized design
write -format verilog -hierarchy -output netlist/${DESIGN_NAME}.syn.v
write_sdf netlist/${DESIGN_NAME}.sdf
# write -format ddc -hierarchy -output netlist/${DESIGN_NAME}.ddc

# Exit DC
exit