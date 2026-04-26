set DESIGN_NAME_GOLDEN "design_name_golden_here"
set DESIGN_NAME "design_name_here"
set TOP_NAME "design_top_here"


clear -all
check_sec -analyze -spec -sv ./rtl/${DESIGN_NAME_GOLDEN}.design_tpe_here
check_sec -analyze -imp -sv ./rtl/${DESIGN_NAME}.design_tpe_here
check_sec -elaborate -spec -top ${TOP_NAME} -disable_auto_bbox
check_sec -elaborate -imp -top ${TOP_NAME} -disable_auto_bbox
# check_sec -setup clock -infer reset -none
check_sec -setup 
check_sec -map -auto
clock design_clk_here 
reset design_rst_here
check_sec -gen
# check_sec -prove -strategy design_style -design_style_type clock_gating
# check_sec -prove
check_sec -prove -strategy proof