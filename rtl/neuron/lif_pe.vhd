library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity lif_pe is
  generic (
    MEM_WIDTH  : positive := 16;
    ACC_WIDTH  : positive := 24;
    BETA_SHIFT : natural  := 4
  );
  port (
    clk       : in  std_logic;
    reset     : in  std_logic;
    valid     : in  std_logic;
    current   : in  signed(ACC_WIDTH - 1 downto 0);
    threshold : in  signed(MEM_WIDTH - 1 downto 0);
    spike     : out std_logic;
    membrane  : out signed(MEM_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of lif_pe is
  signal membrane_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  constant MEM_MAX : signed(MEM_WIDTH - 1 downto 0) :=
    ('0', others => '1');
  constant MEM_MIN : signed(MEM_WIDTH - 1 downto 0) :=
    ('1', others => '0');
begin
  membrane <= membrane_reg;

  update_state : process (clk)
    variable extended_membrane : signed(ACC_WIDTH downto 0);
    variable leaked            : signed(ACC_WIDTH downto 0);
    variable candidate_wide    : signed(ACC_WIDTH downto 0);
    variable candidate         : signed(MEM_WIDTH - 1 downto 0);
  begin
    if rising_edge(clk) then
      if reset = '1' then
        membrane_reg <= (others => '0');
        spike <= '0';
      elsif valid = '1' then
        extended_membrane := resize(membrane_reg, ACC_WIDTH + 1);
        leaked := extended_membrane - shift_right(extended_membrane, BETA_SHIFT);
        candidate_wide := leaked + resize(current, ACC_WIDTH + 1);

        if candidate_wide > resize(MEM_MAX, ACC_WIDTH + 1) then
          candidate := MEM_MAX;
        elsif candidate_wide < resize(MEM_MIN, ACC_WIDTH + 1) then
          candidate := MEM_MIN;
        else
          candidate := resize(candidate_wide, MEM_WIDTH);
        end if;

        if candidate >= threshold then
          membrane_reg <= candidate - threshold;
          spike <= '1';
        else
          membrane_reg <= candidate;
          spike <= '0';
        end if;
      else
        spike <= '0';
      end if;
    end if;
  end process;
end architecture;
