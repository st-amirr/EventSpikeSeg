library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- One externally state-backed temporal class-current transaction.
--
-- scores_i is the current 11-class vector for one pixel.  One final hidden
-- spike supplies a packed signed contribution vector selected from the
-- replaceable 16x11 readout ROM.  At prediction flush, zero contributions may
-- be supplied to classify and reclaim an existing sparse pixel entry.
entity class_current_update is
  generic (
    CLASS_COUNT        : positive := 11;
    SCORE_WIDTH        : positive := 24;
    CONTRIBUTION_WIDTH : positive := 8;
    CLASS_WIDTH        : positive := 4
  );
  port (
    clk                 : in  std_logic;
    reset               : in  std_logic;
    in_valid            : in  std_logic;
    in_ready            : out std_logic;
    scores_i            : in  std_logic_vector(CLASS_COUNT * SCORE_WIDTH - 1 downto 0);
    contributions_i     : in  std_logic_vector(
      CLASS_COUNT * CONTRIBUTION_WIDTH - 1 downto 0
    );
    prediction_flush_i  : in  std_logic;
    out_valid           : out std_logic;
    out_ready           : in  std_logic;
    scores_o            : out std_logic_vector(CLASS_COUNT * SCORE_WIDTH - 1 downto 0);
    state_live_o        : out std_logic;
    prediction_valid_o  : out std_logic;
    class_o             : out unsigned(CLASS_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of class_current_update is
  signal out_valid_reg        : std_logic := '0';
  signal scores_reg           : std_logic_vector(
    CLASS_COUNT * SCORE_WIDTH - 1 downto 0
  ) := (others => '0');
  signal state_live_reg       : std_logic := '0';
  signal prediction_valid_reg : std_logic := '0';
  signal class_reg            : unsigned(CLASS_WIDTH - 1 downto 0) := (others => '0');

  function saturate_score(value : signed(SCORE_WIDTH downto 0)) return signed is
    variable maximum : signed(SCORE_WIDTH downto 0);
    variable minimum : signed(SCORE_WIDTH downto 0);
  begin
    maximum := to_signed((2 ** (SCORE_WIDTH - 1)) - 1, SCORE_WIDTH + 1);
    minimum := to_signed(-(2 ** (SCORE_WIDTH - 1)), SCORE_WIDTH + 1);
    if value > maximum then
      return to_signed((2 ** (SCORE_WIDTH - 1)) - 1, SCORE_WIDTH);
    elsif value < minimum then
      return to_signed(-(2 ** (SCORE_WIDTH - 1)), SCORE_WIDTH);
    end if;
    return resize(value, SCORE_WIDTH);
  end function;
begin
  assert (2 ** CLASS_WIDTH) >= CLASS_COUNT
    report "CLASS_WIDTH is too small"
    severity failure;
  assert SCORE_WIDTH <= 24
    report "class-current baseline supports SCORE_WIDTH <= 24"
    severity failure;

  in_ready <= not out_valid_reg or out_ready;
  out_valid <= out_valid_reg;
  scores_o <= scores_reg;
  state_live_o <= state_live_reg;
  prediction_valid_o <= prediction_valid_reg;
  class_o <= class_reg;

  update_current : process (clk)
    variable updated_scores : std_logic_vector(
      CLASS_COUNT * SCORE_WIDTH - 1 downto 0
    );
    variable old_score      : signed(SCORE_WIDTH - 1 downto 0);
    variable contribution   : signed(CONTRIBUTION_WIDTH - 1 downto 0);
    variable sum_wide       : signed(SCORE_WIDTH downto 0);
    variable updated_score  : signed(SCORE_WIDTH - 1 downto 0);
    variable best_score     : signed(SCORE_WIDTH - 1 downto 0);
    variable best_index     : natural range 0 to CLASS_COUNT - 1;
    variable any_live       : boolean;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        out_valid_reg <= '0';
        scores_reg <= (others => '0');
        state_live_reg <= '0';
        prediction_valid_reg <= '0';
        class_reg <= (others => '0');
      elsif out_valid_reg = '0' or out_ready = '1' then
        out_valid_reg <= in_valid;
        prediction_valid_reg <= '0';
        if in_valid = '1' then
          updated_scores := (others => '0');
          best_index := 0;
          best_score := (others => '0');
          any_live := false;
          for class_index in 0 to CLASS_COUNT - 1 loop
            old_score := signed(
              scores_i((class_index + 1) * SCORE_WIDTH - 1
                downto class_index * SCORE_WIDTH)
            );
            contribution := signed(
              contributions_i((class_index + 1) * CONTRIBUTION_WIDTH - 1
                downto class_index * CONTRIBUTION_WIDTH)
            );
            sum_wide := resize(old_score, SCORE_WIDTH + 1)
              + resize(contribution, SCORE_WIDTH + 1);
            updated_score := saturate_score(sum_wide);
            updated_scores((class_index + 1) * SCORE_WIDTH - 1
              downto class_index * SCORE_WIDTH) := std_logic_vector(updated_score);
            if updated_score /= to_signed(0, SCORE_WIDTH) then
              any_live := true;
            end if;
            if class_index = 0 or updated_score > best_score then
              best_score := updated_score;
              best_index := class_index;
            end if;
          end loop;

          class_reg <= to_unsigned(best_index, CLASS_WIDTH);
          prediction_valid_reg <= prediction_flush_i;
          if prediction_flush_i = '1' then
            -- The prediction window ends here; only class output survives.
            scores_reg <= (others => '0');
            state_live_reg <= '0';
          else
            scores_reg <= updated_scores;
            if any_live then
              state_live_reg <= '1';
            else
              state_live_reg <= '0';
            end if;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
