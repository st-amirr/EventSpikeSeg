library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Externally state-backed touched-neuron PLIF lane for 5 ms binned streaming.
--
-- elapsed_bins_i is the modular distance between the current global bin tag and
-- the stored last-bin tag.  To preserve the training semantics exactly, the
-- baseline applies the exported learned beta once per elapsed bin before adding
-- the current accumulated for the present bin.  This iterative implementation
-- deliberately trades cycles for simple/bit-exact behavior; a beta^delta LUT or
-- exponentiation unit may replace it later only after equivalence is verified.
entity plif_update is
  generic (
    MEM_WIDTH      : positive := 16;
    CURRENT_WIDTH  : positive := 24;
    BETA_WIDTH     : positive := 16;
    BETA_FRAC_BITS : natural  := 15;
    DELTA_WIDTH    : positive := 24
  );
  port (
    clk            : in  std_logic;
    reset          : in  std_logic;
    in_valid       : in  std_logic;
    in_ready       : out std_logic;
    membrane_i     : in  signed(MEM_WIDTH - 1 downto 0);
    current_i      : in  signed(CURRENT_WIDTH - 1 downto 0);
    beta_i         : in  unsigned(BETA_WIDTH - 1 downto 0);
    threshold_i    : in  signed(MEM_WIDTH - 1 downto 0);
    elapsed_bins_i : in  unsigned(DELTA_WIDTH - 1 downto 0);
    out_valid      : out std_logic;
    out_ready      : in  std_logic;
    candidate_o    : out signed(MEM_WIDTH - 1 downto 0);
    membrane_o     : out signed(MEM_WIDTH - 1 downto 0);
    spike_o        : out std_logic
  );
end entity;

architecture rtl of plif_update is
  type state_t is (idle, leak, charge, hold_result);
  signal state_reg : state_t := idle;

  signal work_mem_reg  : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal current_reg   : signed(CURRENT_WIDTH - 1 downto 0) := (others => '0');
  signal beta_reg      : unsigned(BETA_WIDTH - 1 downto 0) := (others => '0');
  signal threshold_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal remaining_reg : natural := 0;

  signal candidate_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal membrane_reg  : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal spike_reg     : std_logic := '0';

  function round_divide_ties_away(value : integer; divisor : positive) return integer is
  begin
    if value >= 0 then
      return (value + divisor / 2) / divisor;
    end if;
    return -((-value + divisor / 2) / divisor);
  end function;

  function saturate_mem(value : integer) return integer is
    constant MAXIMUM : integer := (2 ** (MEM_WIDTH - 1)) - 1;
    constant MINIMUM : integer := -(2 ** (MEM_WIDTH - 1));
  begin
    if value > MAXIMUM then
      return MAXIMUM;
    elsif value < MINIMUM then
      return MINIMUM;
    end if;
    return value;
  end function;
begin
  assert MEM_WIDTH <= 16 and CURRENT_WIDTH <= 24 and BETA_WIDTH <= 16
    report "plif_update integer baseline supports at most 16/24/16-bit arithmetic ports"
    severity failure;
  assert BETA_FRAC_BITS < BETA_WIDTH
    report "BETA_FRAC_BITS must be smaller than BETA_WIDTH"
    severity failure;
  assert DELTA_WIDTH <= 30
    report "DELTA_WIDTH must fit the VHDL integer range"
    severity failure;

  in_ready <= '1' when state_reg = idle else '0';
  out_valid <= '1' when state_reg = hold_result else '0';
  candidate_o <= candidate_reg;
  membrane_o <= membrane_reg;
  spike_o <= spike_reg;

  update_fsm : process (clk)
    variable product_value   : integer;
    variable leaked_value    : integer;
    variable candidate_value : integer;
    variable membrane_value  : integer;
    variable elapsed_value   : natural;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        state_reg <= idle;
        work_mem_reg <= (others => '0');
        current_reg <= (others => '0');
        beta_reg <= (others => '0');
        threshold_reg <= (others => '0');
        remaining_reg <= 0;
        candidate_reg <= (others => '0');
        membrane_reg <= (others => '0');
        spike_reg <= '0';
      else
        case state_reg is
          when idle =>
            spike_reg <= '0';
            if in_valid = '1' then
              work_mem_reg <= membrane_i;
              current_reg <= current_i;
              beta_reg <= beta_i;
              threshold_reg <= threshold_i;
              elapsed_value := to_integer(elapsed_bins_i);
              remaining_reg <= elapsed_value;
              if elapsed_value = 0 then
                state_reg <= charge;
              else
                state_reg <= leak;
              end if;
            end if;

          when leak =>
            product_value := to_integer(work_mem_reg) * to_integer(beta_reg);
            leaked_value := saturate_mem(
              round_divide_ties_away(product_value, 2 ** BETA_FRAC_BITS)
            );
            work_mem_reg <= to_signed(leaked_value, MEM_WIDTH);
            if remaining_reg <= 1 then
              remaining_reg <= 0;
              state_reg <= charge;
            else
              remaining_reg <= remaining_reg - 1;
            end if;

          when charge =>
            candidate_value := saturate_mem(
              to_integer(work_mem_reg) + to_integer(current_reg)
            );
            candidate_reg <= to_signed(candidate_value, MEM_WIDTH);
            if candidate_value >= to_integer(threshold_reg) then
              membrane_value := saturate_mem(
                candidate_value - to_integer(threshold_reg)
              );
              membrane_reg <= to_signed(membrane_value, MEM_WIDTH);
              spike_reg <= '1';
            else
              membrane_reg <= to_signed(candidate_value, MEM_WIDTH);
              spike_reg <= '0';
            end if;
            state_reg <= hold_result;

          when hold_result =>
            if out_ready = '1' then
              state_reg <= idle;
            end if;
        end case;
      end if;
    end if;
  end process;
end architecture;
