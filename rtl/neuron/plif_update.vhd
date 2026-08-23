library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- One externally state-backed PLIF update lane. The layer actor/cache supplies
-- membrane_i and writes membrane_o back to the logical-neuron state store.
-- retention_i is exported beta**(delta_us/5000us) in UQ1.15.
entity plif_update is
  generic (
    MEM_WIDTH      : positive := 16;
    CURRENT_WIDTH  : positive := 24;
    BETA_WIDTH     : positive := 16;
    BETA_FRAC_BITS : natural  := 15
  );
  port (
    clk         : in  std_logic;
    reset       : in  std_logic;
    in_valid    : in  std_logic;
    in_ready    : out std_logic;
    membrane_i  : in  signed(MEM_WIDTH - 1 downto 0);
    current_i   : in  signed(CURRENT_WIDTH - 1 downto 0);
    retention_i : in  unsigned(BETA_WIDTH - 1 downto 0);
    threshold_i : in  signed(MEM_WIDTH - 1 downto 0);
    out_valid   : out std_logic;
    out_ready   : in  std_logic;
    candidate_o : out signed(MEM_WIDTH - 1 downto 0);
    membrane_o  : out signed(MEM_WIDTH - 1 downto 0);
    spike_o     : out std_logic
  );
end entity;

architecture rtl of plif_update is
  signal out_valid_reg  : std_logic := '0';
  signal candidate_reg  : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal membrane_reg   : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal spike_reg      : std_logic := '0';

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
    report "plif_update integer baseline supports at most 16/24/16-bit ports"
    severity failure;
  assert BETA_FRAC_BITS < BETA_WIDTH
    report "BETA_FRAC_BITS must be smaller than BETA_WIDTH"
    severity failure;

  in_ready <= not out_valid_reg or out_ready;
  out_valid <= out_valid_reg;
  candidate_o <= candidate_reg;
  membrane_o <= membrane_reg;
  spike_o <= spike_reg;

  update_pipeline : process (clk)
    variable product_value   : integer;
    variable leaked_value    : integer;
    variable candidate_value : integer;
    variable membrane_value  : integer;
    variable threshold_value : integer;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        out_valid_reg <= '0';
        candidate_reg <= (others => '0');
        membrane_reg <= (others => '0');
        spike_reg <= '0';
      elsif (not out_valid_reg or out_ready) = '1' then
        out_valid_reg <= in_valid;
        if in_valid = '1' then
          product_value := to_integer(membrane_i) * to_integer(retention_i);
          leaked_value := round_divide_ties_away(product_value, 2 ** BETA_FRAC_BITS);
          candidate_value := saturate_mem(leaked_value + to_integer(current_i));
          threshold_value := to_integer(threshold_i);
          candidate_reg <= to_signed(candidate_value, MEM_WIDTH);
          if candidate_value >= threshold_value then
            membrane_value := saturate_mem(candidate_value - threshold_value);
            membrane_reg <= to_signed(membrane_value, MEM_WIDTH);
            spike_reg <= '1';
          else
            membrane_reg <= to_signed(candidate_value, MEM_WIDTH);
            spike_reg <= '0';
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
