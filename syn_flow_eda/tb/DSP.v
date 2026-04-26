module DSP_tb ();
    reg clk, carryIn_tb, rstA_tb, rstB_tb, rstC_tb, rstCarryIn_tb, rstD_tb, rstM_tb, rstOpMode_tb, rstP_tb,
            CEA_tb, CEB_tb, CEC_tb, CECarryIn_tb, CED_tb, CEM_tb, CEOpMode_tb, CEP_tb;
    reg [17:0] A_tb, B_tb, D_tb, BCIn_tb;
    reg [47:0] C_tb, PCIn_tb;
    reg [7:0] opMode_tb;

    wire carryOut_dut, carryOutF_dut;
    wire [17:0] BCOut_dut;
    wire [47:0] PCOut_dut, P_dut;
    wire [35:0] M_dut;

    reg carryOut_exp, carryOutF_exp;
    reg [17:0] BCOut_exp;
    reg [47:0] PCOut_exp, P_exp;
    reg [35:0] M_exp;
    
    // Test result
    reg all_pass;

    DSP dut (clk, opMode_tb, CEA_tb, CEB_tb, CEC_tb, CECarryIn_tb, CED_tb, CEM_tb, CEOpMode_tb, CEP_tb,
                rstA_tb, rstB_tb, rstC_tb, rstCarryIn_tb, rstD_tb, rstM_tb, rstOpMode_tb, rstP_tb,
                A_tb, B_tb, D_tb, C_tb, carryIn_tb, BCIn_tb, PCIn_tb,
                BCOut_dut, PCOut_dut, P_dut, M_dut, carryOut_dut, carryOutF_dut);

    initial begin
        clk = 0;
        forever begin
            #1 clk = ~clk;
        end
    end

    initial begin
        all_pass = 1;
        
        rstA_tb = 1;
        rstB_tb = 1;
        rstC_tb = 1;
        rstCarryIn_tb = 1;
        rstD_tb = 1;
        rstM_tb = 1;
        rstOpMode_tb = 1;
        rstP_tb = 1;
        
        CEA_tb = $random;
        CEB_tb = $random;
        CEC_tb = $random;
        CECarryIn_tb = $random;
        CED_tb = $random;
        CEM_tb = $random;
        CEOpMode_tb = $random;
        CEP_tb = $random;
        
        carryIn_tb = $random;
        A_tb = $random;
        B_tb = $random;
        D_tb = $random;
        BCIn_tb = $random;
        C_tb = $random;
        PCIn_tb = $random;
        opMode_tb = $random;

        carryOut_exp = 0;
        carryOutF_exp = 0;
        BCOut_exp = 0;
        PCOut_exp = 0;
        P_exp = 0;
        M_exp = 0;

        @(negedge clk);

        if (carryOut_dut != carryOut_exp || carryOutF_dut != carryOutF_exp
            || BCOut_dut != BCOut_exp || PCOut_dut != PCOut_exp
            || P_dut != P_exp || M_dut != M_exp) begin
            all_pass = 0;
        end

        rstA_tb = 0;
        rstB_tb = 0;
        rstC_tb = 0;
        rstCarryIn_tb = 0;
        rstD_tb = 0;
        rstM_tb = 0;
        rstOpMode_tb = 0;
        rstP_tb = 0;
        
        CEA_tb = 1;
        CEB_tb = 1;
        CEC_tb = 1;
        CECarryIn_tb = 1;
        CED_tb = 1;
        CEM_tb = 1;
        CEOpMode_tb = 1;
        CEP_tb = 1;

        carryIn_tb = $random;
        A_tb = 20;
        B_tb = 10;
        D_tb = 25;
        BCIn_tb = $random;
        C_tb = 350;
        PCIn_tb = $random;
        opMode_tb = 8'b1101_1101;

        carryOut_exp = 0;
        carryOutF_exp = 0;
        BCOut_exp = 'hf;
        PCOut_exp = 'h32;
        P_exp = 'h32;
        M_exp = 'h12c;

        repeat (4) begin
            @(negedge clk);
        end

        if (carryOut_dut != carryOut_exp || carryOutF_dut != carryOutF_exp
            || BCOut_dut != BCOut_exp || PCOut_dut != PCOut_exp
            || P_dut != P_exp || M_dut != M_exp) begin
            all_pass = 0;
        end

        carryIn_tb = $random;
        A_tb = 20;
        B_tb = 10;
        D_tb = 25;
        BCIn_tb = $random;
        C_tb = 350;
        PCIn_tb = $random;
        opMode_tb = 8'b0001_0000;

        carryOut_exp = 0;
        carryOutF_exp = 0;
        BCOut_exp = 'h23;
        PCOut_exp = 0;
        P_exp = 0;
        M_exp = 'h2bc;

        repeat (3) begin
            @(negedge clk);
        end

        if (carryOut_dut != carryOut_exp || carryOutF_dut != carryOutF_exp
            || BCOut_dut != BCOut_exp || PCOut_dut != PCOut_exp
            || P_dut != P_exp || M_dut != M_exp) begin
            all_pass = 0;
        end

        carryIn_tb = $random;
        A_tb = 20;
        B_tb = 10;
        D_tb = 25;
        BCIn_tb = $random;
        C_tb = 350;
        PCIn_tb = $random;
        opMode_tb = 8'b0000_1010;

        BCOut_exp = 'ha;
        M_exp = 'hc8;

        repeat (3) begin
            @(negedge clk);
        end

        if (carryOut_dut != carryOut_exp || carryOutF_dut != carryOutF_exp
            || BCOut_dut != BCOut_exp || PCOut_dut != PCOut_exp
            || P_dut != P_exp || M_dut != M_exp) begin
            all_pass = 0;
        end

        carryIn_tb = $random;
        A_tb = 5;
        B_tb = 6;
        D_tb = 25;
        BCIn_tb = $random;
        C_tb = 350;
        PCIn_tb = 3000;
        opMode_tb = 8'b1010_0111;

        carryOut_exp = 1;
        carryOutF_exp = 1;
        BCOut_exp = 'h6;
        PCOut_exp = 'hfe6fffec0bb1;
        P_exp = 'hfe6fffec0bb1;
        M_exp = 'h1e;

        repeat (3) begin
            @(negedge clk);
        end

        if (carryOut_dut != carryOut_exp || carryOutF_dut != carryOutF_exp
            || BCOut_dut != BCOut_exp || PCOut_dut != PCOut_exp
            || P_dut != P_exp || M_dut != M_exp) begin
            all_pass = 0;
        end

        if (all_pass)
            $display("PASS");
        else
            $display("FAIL");
            
        $finish;
    end    
endmodule