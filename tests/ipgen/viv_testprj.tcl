set testdir [lindex $argv 0]
set prjdir [lindex $argv 1]
set ipname [lindex $argv 2]
set inputs [lindex $argv 3]
set outputs [lindex $argv 4]
set axilite [lindex $argv 5]

set_param board.repoPaths $testdir/board

create_project testprj $prjdir/testprj -part xczu3cg-sfvc784-1-e
set_property BOARD_PART trenz.biz:te0820_3cg_1e:part0:2.0 [current_project]
set_property  ip_repo_paths  $prjdir/ip [current_project]

update_ip_catalog
create_bd_design "design_1"

create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.2 zynq_ultra_ps_e_0
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1" }  [get_bd_cells zynq_ultra_ps_e_0]
create_bd_cell -type ip -vlnv user.org:user:${ipname}:1.0 ${ipname}_0


if {[llength $inputs] > 0} {
    set_property -dict [list CONFIG.PSU__MAXIGP2__DATA_WIDTH [lindex $inputs 1]] [get_bd_cells zynq_ultra_ps_e_0]
    connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_LPD] [get_bd_intf_pins ${ipname}_0/[lindex $inputs 0]]
    connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins zynq_ultra_ps_e_0/maxihpm0_lpd_aclk]
    set_property -dict [list CONFIG.C_AXI_[string toupper [lindex $inputs 0]]_ID_WIDTH {16}] [get_bd_cells ${ipname}_0]
}

if {[llength $inputs] > 2} {
    set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 {1} CONFIG.PSU__MAXIGP0__DATA_WIDTH [lindex $inputs 3]] [get_bd_cells zynq_ultra_ps_e_0]
    connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_FPD] [get_bd_intf_pins ${ipname}_0/[lindex $inputs 2]]
    connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins zynq_ultra_ps_e_0/maxihpm0_fpd_aclk]
}


if {[llength $axilite] > 0} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_protocol_converter:2.1 axi_protocol_convert_0
    connect_bd_intf_net [get_bd_intf_pins axi_protocol_convert_0/M_AXI] [get_bd_intf_pins ${ipname}_0/[lindex $axilite 0]]
    set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 {1} CONFIG.PSU__MAXIGP0__DATA_WIDTH {32}] [get_bd_cells zynq_ultra_ps_e_0]
    connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_FPD] [get_bd_intf_pins axi_protocol_convert_0/S_AXI]
    connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins zynq_ultra_ps_e_0/maxihpm0_fpd_aclk]
    connect_bd_net [get_bd_pins axi_protocol_convert_0/aclk] [get_bd_pins zynq_ultra_ps_e_0/pl_clk0]
    connect_bd_net [get_bd_pins axi_protocol_convert_0/aresetn] [get_bd_pins zynq_ultra_ps_e_0/pl_resetn0]
}

if {[llength $outputs] > 0} {
    set_property -dict [list CONFIG.PSU__USE__S_AXI_GP2 {1} CONFIG.PSU__SAXIGP2__DATA_WIDTH [lindex $outputs 1]] [get_bd_cells zynq_ultra_ps_e_0]
    connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/S_AXI_HP0_FPD] [get_bd_intf_pins ${ipname}_0/[lindex $outputs 0]]
    connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins zynq_ultra_ps_e_0/saxihp0_fpd_aclk]
    set_property -dict [list CONFIG.C_AXI_[string toupper [lindex $outputs 0]]_ID_WIDTH {5}] [get_bd_cells ${ipname}_0]
}

connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_resetn0] [get_bd_pins ${ipname}_0/aresetn]
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins ${ipname}_0/aclk]

assign_bd_address

validate_bd_design
save_bd_design

make_wrapper -files [get_files $prjdir/testprj/testprj.srcs/sources_1/bd/design_1/design_1.bd] -top
add_files -norecurse $prjdir/testprj/testprj.srcs/sources_1/bd/design_1/hdl/design_1_wrapper.v
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

file mkdir $prjdir/testprj/testprj.sdk
file copy -force $prjdir/testprj/testprj.runs/impl_1/design_1_wrapper.sysdef $prjdir/testprj/testprj.sdk/design_1_wrapper.hdf
