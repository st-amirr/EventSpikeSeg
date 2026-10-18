// Categorical phase control only. Membrane, weights and adaptation remain analog.
module gf180_analog_bin_sequencer (
 input wire clk, reset_n, start, initialize,
 input wire upstream_complete, phase_done, done_ready,
 output wire start_ready, busy, done,
 output wire init_enable, age_advance, beta_enable, accumulate_enable,
 output wire rms_settle_enable, rms_capture_enable, decision_enable,
 output wire reset_enable, inhibit_enable, adaptation_write_enable, commit_enable,
 output wire [3:0] phase
);
 localparam [3:0] IDLE=0, INIT=1, AGE=2, BETA=3, ACCUM=4,
   RMS_SETTLE=5, RMS_CAPTURE=6, DECIDE=7, RESET=8,
   INHIBIT=9, ADAPT=10, COMMIT=11, DONE=12;
 reg [3:0] state;
 reg ack_armed;
 assign phase=state;
 assign start_ready=(state==IDLE);
 assign busy=(state!=IDLE && state!=DONE);
 assign done=(state==DONE);
 assign init_enable=(state==INIT);
 assign age_advance=(state==AGE);
 assign beta_enable=(state==BETA);
 assign accumulate_enable=(state==ACCUM);
 assign rms_settle_enable=(state==RMS_SETTLE);
 assign rms_capture_enable=(state==RMS_CAPTURE);
 assign decision_enable=(state==DECIDE);
 assign reset_enable=(state==RESET);
 assign inhibit_enable=(state==INHIBIT);
 assign adaptation_write_enable=(state==ADAPT);
 assign commit_enable=(state==COMMIT);
 always @(posedge clk or negedge reset_n) begin
  if (!reset_n) begin state<=IDLE; ack_armed<=0; end
  else begin
   if(state==IDLE) begin
    ack_armed<=0;
    if(start) state<=initialize ? INIT : AGE;
   end else if(state==DONE) begin
    ack_armed<=0;
    if(done_ready) state<=IDLE;
   end else if(state==ACCUM) begin
    ack_armed<=0;
    if(upstream_complete) state<=RMS_SETTLE;
   end else begin
    // Each local phase must observe a fresh low then high acknowledgement.
    // An acknowledgement left high from a prior phase cannot skip a phase.
    if(!phase_done) ack_armed<=1;
    if(phase_done && ack_armed) begin
     ack_armed<=0;
     case(state)
      INIT: state<=AGE;
      AGE: state<=BETA;
      BETA: state<=ACCUM;
      RMS_SETTLE: state<=RMS_CAPTURE;
      RMS_CAPTURE: state<=DECIDE;
      DECIDE: state<=RESET;
      RESET: state<=INHIBIT;
      INHIBIT: state<=ADAPT;
      ADAPT: state<=COMMIT;
      COMMIT: state<=DONE;
      default: state<=IDLE;
     endcase
    end
   end
  end
 end
endmodule
