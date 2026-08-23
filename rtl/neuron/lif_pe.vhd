library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Locally state-resident single-bin PLIF helper. Unlike the historical shift-only LIF PE,
-- it accepts the exported learned beta coefficient. The active DSEC streaming baseline uses
-- sparse externally backed state plus plif_update because touched neurons can skip several
-- 5 ms bins and therefore require beta**delta_bins before charging. Use this helper only
-- where the caller has already guaranteed elapsed_bins = 1.
entity lif_pe is
  generic (
    MEM_WIDTH      : positive := 16;
    ACC_WIDTH      : positive := 24;
    BETA_WIDTH     : positive := 16;
    BETA_FRAC_BITS : natural  := 15
  );
  port (
    clk       : in  std_logic;
    reset     : in  std_logic;
    valid     : in  std_logic;
    current   : in  signed(ACC_WIDTH - 1 downto 0);
    beta      : in  unsigned(BETA_WIDTH - 1 downto 0);
    threshold : in  signed(MEM_WIDTH - 1 downto 0);
    spike     : out std_logic;
    membrane  : out signed(MEM_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of lif_pe is
  signal membrane_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');

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
  membrane <= membrane_reg;

  update_state : process (clk)
    variable product_value   : integer;
    variable leaked_value    : integer;
    variable candidate_value : integer;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        membrane_reg <= (others => '0');
        spike <= '0';
      elsif valid = '1' then
        product_value := to_integer(membrane_reg) * to_integer(beta);
        leaked_value := round_divide_ties_away(product_value, 2 ** BETA_FRAC_BITS);
        candidate_value := saturate_mem(leaked_value + to_integer(current));
        if candidate_value >= to_integer(threshold) then
          membrane_reg <= to_signed(
            saturate_mem(candidate_value - to_integer(threshold)), MEM_WIDTH
          );
          spike <= '1';
        else
          membrane_reg <= to_signed(candidate_value, MEM_WIDTH);
          spike <= '0';
        end if;
      else
        spike <= '0';
      end if;
    end if;
  end process;
end architecture;
