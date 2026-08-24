library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- End-to-end 5 ms streaming scheduler for EventSpikeSeg140k v8.
--
-- A sealed input bin is accepted only when the previous bin has traversed all
-- deployed actors.  Ingress is expected to use two alternating buffers so the
-- camera can fill bin n+1 while this controller processes bin n.  The controller
-- counts compute cycles for each bin and reports both the hard real-time deadline
-- (U <= 1.0) and the preferred utilization target (default U <= 0.8).
entity streaming_bin_controller is
  generic (
    ACTOR_COUNT             : positive := 25;
    PREDICTION_BINS         : positive := 10;
    ACTOR_INDEX_WIDTH       : positive := 5;
    BIN_TAG_WIDTH           : positive := 24;
    CYCLE_COUNT_WIDTH       : positive := 24;
    CLOCK_KHZ               : positive := 100000;
    BIN_US                  : positive := 5000;
    TARGET_UTIL_NUMERATOR   : positive := 4;
    TARGET_UTIL_DENOMINATOR : positive := 5
  );
  port (
    clk                    : in  std_logic;
    reset                  : in  std_logic;
    bin_valid_i            : in  std_logic;
    bin_ready_o            : out std_logic;
    bin_buffer_i           : in  std_logic;
    actor_advance_i        : in  std_logic;
    active_o               : out std_logic;
    actor_index_o          : out unsigned(ACTOR_INDEX_WIDTH - 1 downto 0);
    current_bin_tag_o      : out unsigned(BIN_TAG_WIDTH - 1 downto 0);
    active_buffer_o        : out std_logic;
    bin_done_o             : out std_logic;
    prediction_due_o       : out std_logic;
    hard_deadline_miss_o   : out std_logic;
    target_budget_miss_o   : out std_logic;
    bin_cycles_o           : out unsigned(CYCLE_COUNT_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of streaming_bin_controller is
  -- CLOCK_KHZ * BIN_US / 1000 avoids overflowing the minimum VHDL integer range
  -- for ordinary FPGA clocks while still giving the exact cycle count for 5 ms.
  constant HARD_CYCLE_BUDGET : natural := (CLOCK_KHZ * BIN_US) / 1000;
  constant TARGET_CYCLE_BUDGET : natural :=
    (HARD_CYCLE_BUDGET * TARGET_UTIL_NUMERATOR) / TARGET_UTIL_DENOMINATOR;

  signal active_reg          : std_logic := '0';
  signal actor_index_reg     : natural range 0 to ACTOR_COUNT - 1 := 0;
  signal bin_tag_reg         : unsigned(BIN_TAG_WIDTH - 1 downto 0) := (others => '0');
  signal buffer_reg          : std_logic := '0';
  signal prediction_count_reg: natural range 0 to PREDICTION_BINS - 1 := 0;
  signal cycle_count_reg     : natural := 0;
  signal completed_cycles_reg: natural := 0;

  signal bin_done_reg           : std_logic := '0';
  signal prediction_due_reg     : std_logic := '0';
  signal hard_deadline_miss_reg : std_logic := '0';
  signal target_budget_miss_reg : std_logic := '0';
begin
  assert (2 ** ACTOR_INDEX_WIDTH) >= ACTOR_COUNT
    report "ACTOR_INDEX_WIDTH is too small"
    severity failure;
  assert TARGET_UTIL_NUMERATOR <= TARGET_UTIL_DENOMINATOR
    report "target utilization must not exceed 1.0"
    severity failure;
  assert HARD_CYCLE_BUDGET > 0
    report "invalid hard cycle budget"
    severity failure;
  assert (2 ** CYCLE_COUNT_WIDTH) > HARD_CYCLE_BUDGET
    report "CYCLE_COUNT_WIDTH cannot represent one bin deadline"
    severity failure;

  bin_ready_o <= not active_reg;
  active_o <= active_reg;
  actor_index_o <= to_unsigned(actor_index_reg, ACTOR_INDEX_WIDTH);
  current_bin_tag_o <= bin_tag_reg;
  active_buffer_o <= buffer_reg;
  bin_done_o <= bin_done_reg;
  prediction_due_o <= prediction_due_reg;
  hard_deadline_miss_o <= hard_deadline_miss_reg;
  target_budget_miss_o <= target_budget_miss_reg;
  bin_cycles_o <= to_unsigned(completed_cycles_reg, CYCLE_COUNT_WIDTH);

  schedule : process (clk)
    variable final_cycles : natural;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        active_reg <= '0';
        actor_index_reg <= 0;
        bin_tag_reg <= (others => '0');
        buffer_reg <= '0';
        prediction_count_reg <= 0;
        cycle_count_reg <= 0;
        completed_cycles_reg <= 0;
        bin_done_reg <= '0';
        prediction_due_reg <= '0';
        hard_deadline_miss_reg <= '0';
        target_budget_miss_reg <= '0';
      else
        bin_done_reg <= '0';
        prediction_due_reg <= '0';
        hard_deadline_miss_reg <= '0';
        target_budget_miss_reg <= '0';

        if active_reg = '0' then
          if bin_valid_i = '1' then
            active_reg <= '1';
            actor_index_reg <= 0;
            buffer_reg <= bin_buffer_i;
            cycle_count_reg <= 0;
          end if;
        else
          cycle_count_reg <= cycle_count_reg + 1;
          if actor_advance_i = '1' then
            if actor_index_reg < ACTOR_COUNT - 1 then
              actor_index_reg <= actor_index_reg + 1;
            else
              final_cycles := cycle_count_reg + 1;
              completed_cycles_reg <= final_cycles;
              active_reg <= '0';
              actor_index_reg <= 0;
              bin_done_reg <= '1';
              if final_cycles > HARD_CYCLE_BUDGET then
                hard_deadline_miss_reg <= '1';
              end if;
              if final_cycles > TARGET_CYCLE_BUDGET then
                target_budget_miss_reg <= '1';
              end if;

              if prediction_count_reg = PREDICTION_BINS - 1 then
                prediction_count_reg <= 0;
                prediction_due_reg <= '1';
              else
                prediction_count_reg <= prediction_count_reg + 1;
              end if;
              bin_tag_reg <= bin_tag_reg + 1;
            end if;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
