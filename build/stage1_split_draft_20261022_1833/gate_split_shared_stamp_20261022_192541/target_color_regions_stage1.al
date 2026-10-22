<?xml version="1.0" encoding="UTF-8"?>
<Project Version="3" Minor="2" Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_split_draft_20261022_1833/gate_split_shared_stamp_20261022_192541">
    <Project_Created_Time />
    <TD_Encoding>UTF-8</TD_Encoding>
    <TD_Version>6.2.168116</TD_Version>
    <Name>target_color_regions_stage1</Name>
    <HardWare>
        <Family>PH1</Family>
        <Device>PH1P35MDG324</Device>
        <Speed>-3</Speed>
    </HardWare>
    <Source_Files>
        <Verilog>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_split_draft_20261022_1833/gate_split_shared_stamp_20261022_192541/serial_wrapper.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="0" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/rtl/color_regions/stage1_arith.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="1" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/rtl/color_regions/stage1_sequence.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="2" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_shared_vertex_20261022/stage1_point.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="3" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/rtl/color_regions/stage1_segment.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="4" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_shared_vertex_20261022/stage1_validate.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="5" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_split_draft_20261022_1833/stage1_regions_shared.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="6" />
                </FileInfo>
            </File>
            <File Path="D:/aaa_FPGA/region-sequence-stage1/build/stage1_split_draft_20261022_1833/stage1_render_stamp.v">
                <FileInfo>
                    <Attr Name="UsedInSyn" Val="true" />
                    <Attr Name="UsedInP&R" Val="true" />
                    <Attr Name="BelongTo" Val="design_1" />
                    <Attr Name="CompileOrder" Val="7" />
                </FileInfo>
            </File>
            </Verilog>
        <System_Verilog>
            </System_Verilog>
        <ADC_FILE>
            </ADC_FILE>
        <SDC_FILE>
            </SDC_FILE>
        <IP_FILE>
            </IP_FILE>
    </Source_Files>
    <FileSets>
        <FileSet Name="design_1" Type="DesignFiles">
        </FileSet>
        <FileSet Name="constraint_1" Type="ConstrainFiles">
        </FileSet>
    </FileSets>
    <TOP_MODULE>
        <LABEL>criticalwork_top</LABEL>
        <MODULE>criticalwork_top</MODULE>
        <CREATEINDEX>user</CREATEINDEX>
    </TOP_MODULE>
    <Property>
    </Property>
    <Device_Settings>
    </Device_Settings>
    <Configurations>
        <Control0>
            <mclk_freq>33MHz</mclk_freq>
        </Control0>
        <FeatureRow>
            <boot_mode>mspix4</boot_mode>
        </FeatureRow>
    </Configurations>
    <Runs>
        <Run Name="syn_1" Type="Synthesis" ConstraintSet="constraint_1" Description="" Active="true" useDefaultScript="false">
            <Strategy Name="Default_Synthesis_Strategy">
            </Strategy>
            <UserParams>
            </UserParams>
        </Run>
        <Run Name="phy_1" Type="PhysicalDesign" ConstraintSet="constraint_1" Description="" SynRun="syn_1" Active="true">
            <Strategy Name="Default_PhysicalDesign_Strategy">
                <BitgenProperty::GeneralOption>
                    <compress>on</compress>
                </BitgenProperty::GeneralOption>
            </Strategy>
            <UserParams>
            </UserParams>
        </Run>
    </Runs>
    <Project_Settings>
    </Project_Settings>
</Project>