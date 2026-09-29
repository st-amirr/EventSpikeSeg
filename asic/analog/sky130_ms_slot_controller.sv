// Digital glue for one multiplexed SKY130 mixed-signal PLIF channel.
// Analog comparator and R-2R DAC remain external and are not idealized here.
// SAR feedback must settle before sar_compare_valid is asserted.
module sky130_ms_sar24_writeback (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic        sample_done,
    input  logic        compare_valid,
    input  logic        state_ge_dac,
    output logic        busy,
    output logic        sample_en,
    output logic        compare_en,
    output logic [23:0] dac_code,
    output logic [23:0] q716_code,
    output logic        valid
);
    typedef enum logic [1:0] {S_IDLE, S_SAMPLE, S_TRIAL, S_DONE} state_t;
    state_t state;
    logic [23:0] sar;
    logic [4:0] bit_index;
    logic signed [24:0] q716_scaled;

    always_comb begin
        busy = (state != S_IDLE) && (state != S_DONE);
        sample_en = state == S_SAMPLE;
        compare_en = state == S_TRIAL;
        // Hold the current prefix plus the trial bit at the external DAC.
        dac_code = (state == S_TRIAL) ? (sar | (24'h000001 << bit_index)) : sar;
        valid = state == S_DONE;
        // Invert the restore controller's uniform TT code offset for the
        // declared +/-1.0 state window. This is a mathematical inverse only;
        // the measured path remains coarse and is not analog-closed.
        q716_scaled = ($signed({1'b0, sar}) - 25'sh0803100) >>> 7;
        if (sar == 24'hffffff) q716_code = 24'h00ffff;
        else if (q716_scaled < -25'sd65536) q716_code = 24'hff0000;
        else if (q716_scaled > 25'sd65535) q716_code = 24'h00ffff;
        else q716_code = q716_scaled[23:0];
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            sar <= 24'h800000;
            bit_index <= 5'd23;
        end else begin
            case (state)
                S_IDLE: if (start) begin
                    sar <= 24'h800000;
                    bit_index <= 5'd23;
                    state <= S_SAMPLE;
                end
                S_SAMPLE: if (sample_done) begin
                    sar <= 24'h000000;
                    bit_index <= 5'd23;
                    state <= S_TRIAL;
                end
                S_TRIAL: if (compare_valid) begin
                    if (state_ge_dac) sar[bit_index] <= 1'b1;
                    else sar[bit_index] <= 1'b0;
                    if (bit_index == 0) state <= S_DONE;
                    else bit_index <= bit_index - 1'b1;
                end
                S_DONE: state <= S_IDLE;
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

module sky130_ms_slot_controller #(
    parameter integer RESTORE_CYCLES = 2,
    parameter integer INJECT_CYCLES  = 2,
    parameter integer LEAK_CYCLES_MAX = 65535,
    parameter integer SETTLE_CYCLES  = 2
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [15:0] leak_cycles,
    input  logic        adc_sample_done,
    input  logic        adc_compare_valid,
    input  logic        state_ge_dac,
    output logic        restore_en,
    output logic        inject_en,
    output logic        leak_en,
    output logic        sample_en,
    output logic        compare_en,
    output logic        commit,
    output logic        busy,
    output logic        done,
    output logic [23:0] dac_code,
    output logic [23:0] q716_writeback
);
    typedef enum logic [3:0] {P_IDLE, P_RESTORE, P_GAP1, P_INJECT,
        P_GAP2, P_LEAK, P_SETTLE, P_SAMPLE, P_CONVERT, P_COMMIT} phase_t;
    phase_t phase;
    logic [31:0] remaining;
    logic sar_start, sar_busy, sar_valid, sar_sample_en, sar_compare_en;
    logic [23:0] sar_code, sar_q716;

    always_comb begin
        restore_en = phase == P_RESTORE;
        inject_en = phase == P_INJECT;
        leak_en = phase == P_LEAK;
        sample_en = (phase == P_SAMPLE) && sar_sample_en;
        compare_en = (phase == P_CONVERT) && sar_compare_en;
        commit = phase == P_COMMIT;
        done = phase == P_COMMIT;
        busy = phase != P_IDLE;
        dac_code = sar_code;
        q716_writeback = sar_q716;
    end

    sky130_ms_sar24_writeback adc (
        .clk, .rst_n, .start(sar_start), .sample_done(adc_sample_done),
        .compare_valid(adc_compare_valid && phase == P_CONVERT),
        .state_ge_dac, .busy(sar_busy), .sample_en(sar_sample_en),
        .compare_en(sar_compare_en), .dac_code(sar_code),
        .q716_code(sar_q716), .valid(sar_valid)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase <= P_IDLE;
            remaining <= 0;
            sar_start <= 0;
        end else begin
            sar_start <= 0;
            case (phase)
                P_IDLE: if (start) begin
                    remaining <= (RESTORE_CYCLES > 0) ? RESTORE_CYCLES : 1;
                    phase <= P_RESTORE;
                end
                P_RESTORE: if (remaining <= 1) begin remaining <= 1; phase <= P_GAP1; end
                           else remaining <= remaining - 1;
                P_GAP1: begin remaining <= (INJECT_CYCLES > 0) ? INJECT_CYCLES : 1; phase <= P_INJECT; end
                P_INJECT: if (remaining <= 1) begin remaining <= 1; phase <= P_GAP2; end
                          else remaining <= remaining - 1;
                P_GAP2: begin remaining <= (leak_cycles > LEAK_CYCLES_MAX) ? LEAK_CYCLES_MAX : leak_cycles;
                        phase <= (leak_cycles == 0) ? P_SETTLE : P_LEAK; end
                P_LEAK: if (remaining <= 1) begin remaining <= (SETTLE_CYCLES > 0) ? SETTLE_CYCLES : 1; phase <= P_SETTLE; end
                        else remaining <= remaining - 1;
                P_SETTLE: if (remaining <= 1) begin phase <= P_SAMPLE; sar_start <= 1; end
                          else remaining <= remaining - 1;
                P_SAMPLE: if (sar_busy && !sar_sample_en) phase <= P_CONVERT;
                P_CONVERT: if (sar_valid) phase <= P_COMMIT;
                P_COMMIT: phase <= P_IDLE;
                default: phase <= P_IDLE;
            endcase
        end
    end
endmodule
