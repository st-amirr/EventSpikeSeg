`timescale 1ns/1ps
// Categorical access interlock for one native1024page and its analog compute.
// Numeric state and eight captured column values stay in physical capacitors.
// Commands:0 read/restore,1 capture updated compute,2 commit all eight holders,
// 3 explicitly discard the working copy after a read-only operation such as RMS.
// Compute phases are external; a fresh compute_done low/high is required after
// restoration before capture. Timing parameters require loaded analog evidence.
module gf180_analog_page_access_control_v1 #(
  parameter integer QUIET_CYCLES=2,ADDRESS_CYCLES=4,READ_SETUP_CYCLES=4,
  parameter integer READER_CYCLES=400,RESTORE_SETUP_CYCLES=80,COPY_CYCLES=240,
  parameter integer RELEASE_CYCLES=80,CAPTURE_CYCLES=320,COMMIT_CYCLES=320
) (
  input wire clk,reset,command_valid_i,
  output wire command_ready_o,
  input wire [1:0] command_i,
  input wire [6:0] row_address_i,
  input wire [2:0] column_i,
  input wire compute_done_i,
  output wire done_o,input wire done_ready_i,
  output reg fault_o,
  output reg [6:0] page_address_o,
  output wire [7:0] page_select_o,
  output wire page_read_o,page_read_enable_o,page_write_o,
  output wire page_restore_o,page_restoreb_o,
  output wire compute_init_o,compute_initb_o,compute_write_o,compute_writeb_o,
  output wire [7:0] capture_o,captureb_o,
  output wire [7:0] captured_columns_o,
  output wire busy_o
);
  localparam [3:0] IDLE=0,QUIET=1,ADDRESS=2,READ_SETUP=3,READ_SETTLE=4,
    RESTORE_SETUP=5,COPY=6,RELEASE=7,CAPTURE=8,COMMIT=9,DONE=10;
  reg [3:0] state;
  reg [15:0] remaining;
  reg [1:0] operation;
  reg [6:0] pending_address,held_row,restored_row;
  reg [2:0] column,restored_column;
  reg [7:0] captured;
  reg restored,compute_low_seen,compute_qualified;
  wire capture_wait=(command_i==1) && restored && !compute_qualified;
  assign command_ready_o=(state==IDLE) && !fault_o && !capture_wait;
  assign done_o=(state==DONE) && !fault_o;
  assign busy_o=(state!=IDLE) && (state!=DONE);
  assign captured_columns_o=captured;
  assign page_select_o=8'b1<<column;
  assign page_read_o=!fault_o && (state==READ_SETUP || state==READ_SETTLE || state==RESTORE_SETUP || state==COPY);
  assign page_read_enable_o=!fault_o && (state==READ_SETTLE || state==RESTORE_SETUP || state==COPY);
  assign page_restore_o=!fault_o && (state==RESTORE_SETUP || state==COPY);
  assign page_restoreb_o=!page_restore_o;
  assign compute_init_o=page_restore_o;
  assign compute_initb_o=!compute_init_o;
  assign compute_write_o=!fault_o && state==COPY;
  assign compute_writeb_o=!compute_write_o;
  assign page_write_o=!fault_o && state==COMMIT;
  assign capture_o=(!fault_o && state==CAPTURE)?(8'b1<<column):8'b0;
  assign captureb_o=~capture_o;
  wire bad_read=restored || (captured!=0 && row_address_i!=held_row);
  wire bad_capture=!restored || !compute_qualified || row_address_i!=restored_row ||
       column_i!=restored_column || captured[column_i] || (captured!=0 && row_address_i!=held_row);
  wire bad_commit=(captured!=8'hff || row_address_i!=held_row);
  wire bad_discard=!restored || row_address_i!=restored_row || column_i!=restored_column;
  always @(posedge clk) begin
    if(reset) begin
      state<=IDLE;remaining<=0;operation<=0;page_address_o<=0;pending_address<=0;column<=0;
      held_row<=0;restored_row<=0;restored_column<=0;captured<=0;restored<=0;
      compute_low_seen<=0;compute_qualified<=0;fault_o<=0;
    end else if(!fault_o) begin
      if(restored && !compute_qualified) begin
        if(!compute_done_i) compute_low_seen<=1;
        if(compute_done_i && compute_low_seen) compute_qualified<=1;
      end
      case(state)
        IDLE: if(command_valid_i && command_ready_o) begin
          if((command_i==3 && bad_discard) || (command_i==0 && bad_read) ||
             (command_i==1 && bad_capture) || (command_i==2 && bad_commit)) fault_o<=1;
          else begin
            operation<=command_i;pending_address<=row_address_i;column<=column_i;
            state<=QUIET;remaining<=QUIET_CYCLES-1;
            if(command_i==0) begin restored<=0;compute_low_seen<=0;compute_qualified<=0;end
          end
        end
        QUIET: if(remaining!=0) remaining<=remaining-1'b1;
          else begin page_address_o<=pending_address;state<=ADDRESS;remaining<=ADDRESS_CYCLES-1;end
        ADDRESS: if(remaining!=0) remaining<=remaining-1'b1;
          else case(operation)
            0:begin state<=READ_SETUP;remaining<=READ_SETUP_CYCLES-1;end
            1:begin state<=CAPTURE;remaining<=CAPTURE_CYCLES-1;end
            2:begin state<=COMMIT;remaining<=COMMIT_CYCLES-1;end
            3:begin restored<=0;state<=RELEASE;remaining<=RELEASE_CYCLES-1;end
          endcase
        READ_SETUP: if(remaining!=0) remaining<=remaining-1'b1;
          else begin state<=READ_SETTLE;remaining<=READER_CYCLES-1;end
        READ_SETTLE: if(remaining!=0) remaining<=remaining-1'b1;
          else begin state<=RESTORE_SETUP;remaining<=RESTORE_SETUP_CYCLES-1;end
        RESTORE_SETUP: if(remaining!=0) remaining<=remaining-1'b1;
          else begin state<=COPY;remaining<=COPY_CYCLES-1;end
        COPY: if(remaining!=0) remaining<=remaining-1'b1;
          else begin
            state<=RELEASE;remaining<=RELEASE_CYCLES-1;
            restored<=1;restored_row<=page_address_o;restored_column<=column;
            compute_low_seen<=0;compute_qualified<=0;
          end
        CAPTURE: if(remaining!=0) remaining<=remaining-1'b1;
          else begin
            captured[column]<=1;held_row<=page_address_o;restored<=0;
            state<=RELEASE;remaining<=RELEASE_CYCLES-1;
          end
        COMMIT: if(remaining!=0) remaining<=remaining-1'b1;
          else begin captured<=0;restored<=0;state<=RELEASE;remaining<=RELEASE_CYCLES-1;end
        RELEASE: if(remaining!=0) remaining<=remaining-1'b1;else state<=DONE;
        DONE: if(done_ready_i) state<=IDLE;
        default: fault_o<=1;
      endcase
    end
  end
  initial begin
    if(QUIET_CYCLES<1 || ADDRESS_CYCLES<1 || READ_SETUP_CYCLES<1 || READER_CYCLES<1 ||
       RESTORE_SETUP_CYCLES<1 || COPY_CYCLES<1 || RELEASE_CYCLES<1 || CAPTURE_CYCLES<1 || COMMIT_CYCLES<1 ||
       QUIET_CYCLES>65535 || ADDRESS_CYCLES>65535 || READ_SETUP_CYCLES>65535 || READER_CYCLES>65535 ||
       RESTORE_SETUP_CYCLES>65535 || COPY_CYCLES>65535 || RELEASE_CYCLES>65535 || CAPTURE_CYCLES>65535 || COMMIT_CYCLES>65535)
      $error("Every analog access duration must be1..65535clock cycles");
  end
endmodule
