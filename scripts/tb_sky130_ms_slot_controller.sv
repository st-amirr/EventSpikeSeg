`timescale 1ns/1ps
module tb_sky130_ms_slot_controller;
  logic clk=0, rst_n=0, start=0;
  logic [15:0] leak_cycles=3;
  logic adc_sample_done=0, adc_compare_valid=0, state_ge_dac;
  logic restore_en, inject_en, leak_en, sample_en, compare_en, commit, busy, done;
  logic [23:0] dac_code, q716_writeback;
  logic [23:0] target_code;
  integer comparisons=0, sample_cycles=0, commits=0;
  logic saw_restore=0, saw_inject=0, saw_leak=0, saw_sample=0, saw_compare=0;
  always #5 clk=~clk;

  assign state_ge_dac = target_code >= dac_code;
  sky130_ms_slot_controller #(.RESTORE_CYCLES(2), .INJECT_CYCLES(2), .LEAK_CYCLES_MAX(100), .SETTLE_CYCLES(2)) dut (
    .clk, .rst_n, .start, .leak_cycles, .adc_sample_done,
    .adc_compare_valid, .state_ge_dac, .restore_en, .inject_en, .leak_en,
    .sample_en, .compare_en, .commit, .busy, .done, .dac_code, .q716_writeback
  );

  always @(negedge clk) begin
    if (rst_n) begin
      if ((restore_en && inject_en) || (restore_en && leak_en) || (restore_en && sample_en) || (restore_en && compare_en) || (restore_en && commit) ||
          (inject_en && leak_en) || (inject_en && sample_en) || (inject_en && compare_en) || (inject_en && commit) ||
          (leak_en && sample_en) || (leak_en && compare_en) || (leak_en && commit) ||
          (sample_en && compare_en) || (sample_en && commit) || (compare_en && commit))
        $fatal(1, "phase overlap r=%b i=%b l=%b s=%b c=%b commit=%b",restore_en,inject_en,leak_en,sample_en,compare_en,commit);
      saw_restore <= saw_restore | restore_en;
      saw_inject <= saw_inject | inject_en;
      saw_leak <= saw_leak | leak_en;
      saw_sample <= saw_sample | sample_en;
      saw_compare <= saw_compare | compare_en;
      if (inject_en && !saw_restore) $fatal(1,"injection preceded restore");
      if (leak_en && !saw_inject) $fatal(1,"leak preceded injection");
      if (sample_en && !saw_leak) $fatal(1,"sample preceded leak");
      if (compare_en && !saw_sample) $fatal(1,"SAR preceded sample");
      if (commit && !saw_compare) $fatal(1,"commit preceded SAR decisions");
      if (sample_en) begin
        sample_cycles <= sample_cycles+1;
        adc_sample_done <= 1;
      end else adc_sample_done <= 0;
      adc_compare_valid <= compare_en;
      if (compare_en) comparisons <= comparisons+1;
      if (commit) commits <= commits+1;
    end
  end

  task run_target(input logic [23:0] code, input logic [23:0] expected_q);
    integer timeout;
    begin
      target_code=code;
      start=1; @(negedge clk); start=0;
      timeout=0;
      while (!done && timeout<100) begin @(negedge clk); timeout=timeout+1; end
      if (!done) $fatal(1,"slot timed out");
      if (q716_writeback !== expected_q)
        $fatal(1,"writeback mismatch code=%h got=%h expected=%h",code,q716_writeback,expected_q);
      if (comparisons != 24) $fatal(1,"SAR decisions=%0d expected 24",comparisons);
      @(negedge clk);
      comparisons=0;
    end
  endtask

  initial begin
    target_code=0;
    repeat(3) @(negedge clk); rst_n=1;
    run_target(24'h000000,24'hff0000);
    run_target(24'h803100,24'h000000);
    run_target(24'hffffff,24'h00ffff);
    if (!(saw_restore && saw_inject && saw_leak && saw_sample && saw_compare))
      $fatal(1,"phase coverage incomplete");
    if (commits != 3) $fatal(1,"commit count=%0d",commits);
    $display("PASS slot_seq=3 sar_decisions=72 q716_endpoints=verified phase_overlap=0");
    $finish;
  end
endmodule
