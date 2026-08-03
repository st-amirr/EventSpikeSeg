library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity event_accumulator is
  generic (
    WEIGHT_WIDTH : positive := 8;
    ACC_WIDTH    : positive := 24
  );
  port (
    clk                 : in  std_logic;
    reset               : in  std_logic;
    clear               : in  std_logic;
    valid               : in  std_logic;
    weight              : in  signed(WEIGHT_WIDTH - 1 downto 0);
    accumulated_current : out signed(ACC_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of event_accumulator is
  signal accumulator_reg : signed(ACC_WIDTH - 1 downto 0) := (others => '0');
  constant ACC_MAX : signed(ACC_WIDTH - 1 downto 0) :=
    ('0', others => '1');
  constant ACC_MIN : signed(ACC_WIDTH - 1 downto 0) :=
    ('1', others => '0');
begin
  accumulated_current <= accumulator_reg;

  accumulate : process (clk)
    variable sum_wide : signed(ACC_WIDTH downto 0);
  begin
    if rising_edge(clk) then
      if reset = '1' or clear = '1' then
        accumulator_reg <= (others => '0');
      elsif valid = '1' then
        sum_wide := resize(accumulator_reg, ACC_WIDTH + 1)
          + resize(weight, ACC_WIDTH + 1);
        if sum_wide > resize(ACC_MAX, ACC_WIDTH + 1) then
          accumulator_reg <= ACC_MAX;
        elsif sum_wide < resize(ACC_MIN, ACC_WIDTH + 1) then
          accumulator_reg <= ACC_MIN;
        else
          accumulator_reg <= resize(sum_wide, ACC_WIDTH);
        end if;
      end if;
    end if;
  end process;
end architecture;
