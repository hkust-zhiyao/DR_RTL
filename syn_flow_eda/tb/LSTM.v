`timescale 1ns / 1ps

module Test;

	// Inputs
	reg [15:0] c_in;
	reg [15:0] h_in;
	reg [15:0] X;

	// Outputs
	wire [15:0] c_out;
	wire [15:0] h_out;
	
	// Test result
	reg all_pass;

	// Instantiate the Unit Under Test (UUT)
	lstm_cell uut (
		.c_in(c_in), 
		.h_in(h_in), 
		.X(X), 
		.c_out(c_out), 
		.h_out(h_out)
	);

	initial begin
		// Initialize
		all_pass = 1;
		c_in = 0;
		h_in = 0;
		X = 0;

		// Wait 100 ns for global reset to finish
		// Take not too large inputs such that they don't overflow and give proper results after right shift
		// Preferably, take inputs <4 && >-4
		// First 8 bits are integeral part and last 8 bits are fractional
		// All Numbers are signed 
		
		#200;
		// Test 1
		X = -16'h0080;       // X = -0.5
		c_in = -16'h0100;    // c_in = -1
		h_in = 16'h0280;     // h_in = 2.5
		
		#200;
		if (c_out !== 16'd707 || h_out !== 16'd0) begin
			all_pass = 0;
		end
		
		// Test 2
		X = 16'h0110;
		c_in = 16'h0110;
		h_in = 16'h0211;
		
		#200;
		if (c_out !== 16'd65517 || h_out !== 16'd65527) begin
			all_pass = 0;
		end
		
		// Test 3
		X = -16'h0110;
		c_in = 16'h0120;
		h_in = 16'h0011;
		
		#200;
		if (c_out !== 16'd65496 || h_out !== 16'd65517) begin
			all_pass = 0;
		end
		
		// Test 4
		X = 16'h0110;
		c_in = 16'h0210;
		h_in = -16'h0011;
		
		#200;
		if (c_out !== 16'd1001 || h_out !== 16'd256) begin
			all_pass = 0;
		end
		
		if (all_pass)
			$display("PASS");
		else
			$display("FAIL");
			
		$finish;
	end
      
endmodule