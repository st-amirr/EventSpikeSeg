library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity event_conv_address is
  generic (
    COORD_WIDTH   : positive := 10;
    STRIDE_X      : positive := 2;
    STRIDE_Y      : positive := 2;
    PAD_X         : natural  := 1;
    PAD_Y         : natural  := 1;
    OUTPUT_WIDTH  : positive := 120;
    OUTPUT_HEIGHT : positive := 90
  );
  port (
    input_x  : in  unsigned(COORD_WIDTH - 1 downto 0);
    input_y  : in  unsigned(COORD_WIDTH - 1 downto 0);
    kernel_x : in  unsigned(COORD_WIDTH - 1 downto 0);
    kernel_y : in  unsigned(COORD_WIDTH - 1 downto 0);
    valid    : out std_logic;
    output_x : out unsigned(COORD_WIDTH - 1 downto 0);
    output_y : out unsigned(COORD_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of event_conv_address is
begin
  generate_address : process (all)
    variable numerator_x : integer;
    variable numerator_y : integer;
    variable quotient_x  : integer;
    variable quotient_y  : integer;
  begin
    numerator_x := to_integer(input_x) + PAD_X - to_integer(kernel_x);
    numerator_y := to_integer(input_y) + PAD_Y - to_integer(kernel_y);
    quotient_x := 0;
    quotient_y := 0;
    valid <= '0';
    output_x <= (others => '0');
    output_y <= (others => '0');

    if numerator_x >= 0 and numerator_y >= 0 then
      quotient_x := numerator_x / STRIDE_X;
      quotient_y := numerator_y / STRIDE_Y;
      if numerator_x mod STRIDE_X = 0 and numerator_y mod STRIDE_Y = 0
        and quotient_x < OUTPUT_WIDTH and quotient_y < OUTPUT_HEIGHT then
        valid <= '1';
        output_x <= to_unsigned(quotient_x, COORD_WIDTH);
        output_y <= to_unsigned(quotient_y, COORD_WIDTH);
      end if;
    end if;
  end process;
end architecture;
