library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity f_inst_top1 is
  generic (
    CHANNELS : positive := 4;
    WIDTH    : positive := 16
  );
  port (
    candidates     : in  std_logic_vector(CHANNELS * WIDTH - 1 downto 0);
    candidate_mask : in  std_logic_vector(CHANNELS - 1 downto 0);
    winners        : out std_logic_vector(CHANNELS - 1 downto 0)
  );
end entity;

architecture rtl of f_inst_top1 is
begin
  select_winner : process (all)
    variable result       : std_logic_vector(CHANNELS - 1 downto 0);
    variable found        : boolean;
    variable winner_index : natural range 0 to CHANNELS - 1;
    variable value        : signed(WIDTH - 1 downto 0);
    variable best         : signed(WIDTH - 1 downto 0);
  begin
    result := (others => '0');
    found := false;
    winner_index := 0;
    best := (others => '0');
    best(WIDTH - 1) := '1';

    for channel in 0 to CHANNELS - 1 loop
      value := signed(candidates((channel + 1) * WIDTH - 1 downto channel * WIDTH));
      if candidate_mask(channel) = '1' and (not found or value > best) then
        found := true;
        best := value;
        winner_index := channel;
      end if;
    end loop;

    if found then
      result(winner_index) := '1';
    end if;
    winners <= result;
  end process;
end architecture;
