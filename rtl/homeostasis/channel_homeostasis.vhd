library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity channel_homeostasis is
  generic (
    WIDTH       : positive := 16;
    COUNT_WIDTH : positive := 16
  );
  port (
    clk         : in  std_logic;
    reset       : in  std_logic;
    valid       : in  std_logic;
    spike_count : in  unsigned(COUNT_WIDTH - 1 downto 0);
    decay       : in  unsigned(WIDTH - 1 downto 0);
    increment   : in  unsigned(WIDTH - 1 downto 0);
    adaptation  : out unsigned(WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of channel_homeostasis is
  signal adaptation_reg : unsigned(WIDTH - 1 downto 0) := (others => '0');
  constant MAXIMUM : unsigned(WIDTH - 1 downto 0) := (others => '1');
begin
  adaptation <= adaptation_reg;

  update_adaptation : process (clk)
    variable decayed   : unsigned(WIDTH - 1 downto 0);
    variable product   : unsigned(WIDTH + COUNT_WIDTH - 1 downto 0);
    variable next_wide : unsigned(WIDTH + COUNT_WIDTH - 1 downto 0);
  begin
    if rising_edge(clk) then
      if reset = '1' then
        adaptation_reg <= (others => '0');
      elsif valid = '1' then
        if adaptation_reg > decay then
          decayed := adaptation_reg - decay;
        else
          decayed := (others => '0');
        end if;
        product := spike_count * increment;
        next_wide := resize(decayed, next_wide'length) + product;
        if next_wide > resize(MAXIMUM, next_wide'length) then
          adaptation_reg <= MAXIMUM;
        else
          adaptation_reg <= resize(next_wide, WIDTH);
        end if;
      end if;
    end if;
  end process;
end architecture;
