set testdir [lindex $argv 0]
set prjdir [lindex $argv 1]
set testname [lindex $argv 2]

set workspace $prjdir/$testname/$testname.sdk

hsi::set_param board.repoPaths $workspace/hwtest/board/

setws $workspace
createhw -name hwtest -hwspec $workspace/design_1_wrapper.hdf
openhw $workspace/hwtest/system.hdf

createapp -name test -app {Empty Application} -proc psu_cortexa53_0 -hwproject hwtest -os standalone
importsources -name test -path $testdir/$testname

projects -clean -type all
projects -build -type all
