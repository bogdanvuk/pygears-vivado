set testdir [lindex $argv 0]
set prjdir [lindex $argv 1]

connect

set workspace $prjdir/testprj/testprj.sdk

puts "XSDB: loading CPU setup script"
source $workspace/hwtest/psu_init.tcl

puts "XSDB: resetting system"
targets -set -filter {name =~ "APU*"}
rst -system

puts "XSDB: downloading bitstream"
targets -set -filter {level == 0} -index 0
fpga -f $workspace/hwtest/design_1_wrapper.bit
targets -set -filter {name =~ "APU*"}


puts "XSDB: resetting CPU"
after 1000
rst -cores

puts "XSDB: configuring CPU"
configparams force-mem-access 1
puts "XSDB: 1"
targets -set -filter {name =~ "APU*"}
puts "XSDB: 2"
psu_init
after 100
puts "XSDB: 3"
psu_ps_pl_isolation_removal
after 100
puts "XSDB: 4"
psu_ps_pl_reset_config
puts "XSDB: 5"
catch {psu_protection}
puts "XSDB: 6"
targets -set -nocase -filter {name =~ "*A53*0"} -index 1
puts "XSDB: 7"

puts "XSDB: programming CPU"
rst -processor
dow $workspace/test/Debug/test.elf
configparams force-mem-access 0

puts "XSDB: running"
con
