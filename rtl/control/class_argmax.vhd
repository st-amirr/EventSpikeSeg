library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Argmax over signed temporal class-current accumulators for one spatial pixel.
-- Scores are packed class-major, class 0 in the least-significant SCORE_WIDTH bits.
-- The common positive output scaling used by the Python readout is intentionally
-- omitted because it cannot change the winning class.
entity class_argmax is
  generic (
    CLASS_COUNT : positive := 11;
    SCORE_WIDTH : positive := 24;
    CLASS_WIDTH : positive := 4
  );
  port (
    scores_i : in  std_logic_vector(CLASS_COUNT * SCORE_WIDTH - 1 downto 0);
    class_o  : out unsigned(CLASS_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of class_argmax is
begin
  assert (2 ** CLASS_WIDTH) >= CLASS_COUNT
    report "CLASS_WIDTH is too small"
    severity failure;

  select_class : process (all)
    variable best_index : natural range 0 to CLASS_COUNT - 1;
    variable best_score : signed(SCORE_WIDTH - 1 downto 0);
    variable candidate  : signed(SCORE_WIDTH - 1 downto 0);
  begin
    best_index := 0;
    best_score := signed(scores_i(SCORE_WIDTH - 1 downto 0));
    for class_index in 1 to CLASS_COUNT - 1 loop
      candidate := signed(
        scores_i((class_index + 1) * SCORE_WIDTH - 1 downto class_index * SCORE_WIDTH)
      );
      -- PyTorch argmax returns the first index on a tie, so update only on >.
      if candidate > best_score then
        best_score := candidate;
        best_index := class_index;
      end if;
    end loop;
    class_o <= to_unsigned(best_index, CLASS_WIDTH);
  end process;
end architecture;
