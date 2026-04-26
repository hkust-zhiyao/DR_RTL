set search_path [list ./rtl ./lib ]
set target_library [list "nangate.db"]
set DESIGN_NAME "design_name_here"
set DESIGN_NAME_NEW "design_name_new_here"
set TOP_NAME "design_top_here"

read_db -technology_library ./lib/nangate.db

# read_verilog  -r ./input/rtl/${DESIGN_NAME_NEW}/*.v
read_verilog -r ./netlist/${DESIGN_NAME}.v0.syn.v
set_top ${TOP_NAME}

# read_verilog -i ./netlist/${DESIGN_NAME}.syn.v
read_verilog -i ./netlist/${DESIGN_NAME_NEW}.syn.v
set_top ${TOP_NAME}

match

verify

exit