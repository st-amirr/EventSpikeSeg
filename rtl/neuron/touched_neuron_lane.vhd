library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Actor-local transaction lane joining sparse state lookup, exact lazy PLIF
-- decay/update, and lossless state writeback.  Synaptic contributions for one
-- destination must already be accumulated before in_valid is asserted.
entity touched_neuron_lane is
  generic (
    ADDRESS_WIDTH      : positive := 28;
    MEM_WIDTH          : positive := 16;
    CURRENT_WIDTH      : positive := 24;
    BETA_WIDTH         : positive := 16;
    BETA_FRAC_BITS     : natural  := 15;
    ADAPTATION_WIDTH   : positive := 16;
    BIN_TAG_WIDTH      : positive := 24;
    SET_COUNT          : positive := 8;
    WAY_COUNT          : positive := 2;
    COUNT_WIDTH        : positive := 16;
    ADAPTATION_ENABLED : boolean  := false
  );
  port (
    clk                : in  std_logic;
    reset              : in  std_logic;
    in_valid           : in  std_logic;
    in_ready           : out std_logic;
    address_i          : in  unsigned(ADDRESS_WIDTH - 1 downto 0);
    current_i          : in  signed(CURRENT_WIDTH - 1 downto 0);
    beta_i             : in  unsigned(BETA_WIDTH - 1 downto 0);
    threshold_i        : in  signed(MEM_WIDTH - 1 downto 0);
    current_bin_tag_i  : in  unsigned(BIN_TAG_WIDTH - 1 downto 0);
    out_valid          : out std_logic;
    out_ready          : in  std_logic;
    address_o          : out unsigned(ADDRESS_WIDTH - 1 downto 0);
    candidate_o        : out signed(MEM_WIDTH - 1 downto 0);
    membrane_o         : out signed(MEM_WIDTH - 1 downto 0);
    spike_o            : out std_logic;
    state_overflow_o   : out std_logic;
    live_entry_count_o : out unsigned(COUNT_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of touched_neuron_lane is
  type lane_state_t is (
    idle, bank_read_issue, bank_read_wait, plif_issue, plif_wait,
    bank_write_issue, bank_write_wait, hold_result
  );
  signal lane_state_reg : lane_state_t := idle;

  signal address_reg         : unsigned(ADDRESS_WIDTH - 1 downto 0) := (others => '0');
  signal current_reg         : signed(CURRENT_WIDTH - 1 downto 0) := (others => '0');
  signal beta_reg            : unsigned(BETA_WIDTH - 1 downto 0) := (others => '0');
  signal threshold_reg       : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal current_bin_tag_reg : unsigned(BIN_TAG_WIDTH - 1 downto 0) := (others => '0');
  signal stored_membrane_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal stored_age_reg      : signed(ADAPTATION_WIDTH - 1 downto 0) := (others => '1');
  signal stored_amp_reg      : signed(ADAPTATION_WIDTH - 1 downto 0) := (others => '0');
  signal elapsed_bins_reg    : unsigned(BIN_TAG_WIDTH - 1 downto 0) := (others => '0');
  signal candidate_reg       : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal result_membrane_reg : signed(MEM_WIDTH - 1 downto 0) := (others => '0');
  signal result_spike_reg    : std_logic := '0';
  signal overflow_reg        : std_logic := '0';

  signal bank_request_valid  : std_logic;
  signal bank_request_ready  : std_logic;
  signal bank_write_enable   : std_logic;
  signal bank_state_live     : std_logic;
  signal bank_response_valid : std_logic;
  signal bank_found          : std_logic;
  signal bank_overflow       : std_logic;
  signal bank_membrane       : signed(MEM_WIDTH - 1 downto 0);
  signal bank_age            : signed(ADAPTATION_WIDTH - 1 downto 0);
  signal bank_amplitude      : signed(ADAPTATION_WIDTH - 1 downto 0);
  signal bank_last_bin_tag   : unsigned(BIN_TAG_WIDTH - 1 downto 0);

  signal plif_in_valid       : std_logic;
  signal plif_in_ready       : std_logic;
  signal plif_out_valid      : std_logic;
  signal plif_out_ready      : std_logic;
  signal plif_candidate      : signed(MEM_WIDTH - 1 downto 0);
  signal plif_membrane       : signed(MEM_WIDTH - 1 downto 0);
  signal plif_spike          : std_logic;
begin
  in_ready <= '1' when lane_state_reg = idle else '0';
  out_valid <= '1' when lane_state_reg = hold_result else '0';
  address_o <= address_reg;
  candidate_o <= candidate_reg;
  membrane_o <= result_membrane_reg;
  spike_o <= result_spike_reg;
  state_overflow_o <= overflow_reg;

  bank_request_valid <= '1' when
    lane_state_reg = bank_read_issue or lane_state_reg = bank_write_issue
    else '0';
  bank_write_enable <= '1' when lane_state_reg = bank_write_issue else '0';
  bank_state_live <= '1' when
    result_membrane_reg /= to_signed(0, MEM_WIDTH)
    or (ADAPTATION_ENABLED and (
      stored_age_reg >= to_signed(0, ADAPTATION_WIDTH)
      or stored_amp_reg /= to_signed(0, ADAPTATION_WIDTH)
    ))
    else '0';
  plif_in_valid <= '1' when lane_state_reg = plif_issue else '0';
  plif_out_ready <= '1' when lane_state_reg = plif_wait else '0';

  state_bank : entity work.sparse_state_bank
    generic map (
      ADDRESS_WIDTH => ADDRESS_WIDTH,
      MEMBRANE_WIDTH => MEM_WIDTH,
      ADAPTATION_WIDTH => ADAPTATION_WIDTH,
      BIN_TAG_WIDTH => BIN_TAG_WIDTH,
      SET_COUNT => SET_COUNT,
      WAY_COUNT => WAY_COUNT,
      COUNT_WIDTH => COUNT_WIDTH
    )
    port map (
      clk => clk,
      reset => reset,
      request_valid => bank_request_valid,
      request_ready => bank_request_ready,
      write_enable => bank_write_enable,
      address_i => address_reg,
      state_live_i => bank_state_live,
      membrane_i => result_membrane_reg,
      adaptation_age_i => stored_age_reg,
      adaptation_amplitude_i => stored_amp_reg,
      last_bin_tag_i => current_bin_tag_reg,
      response_valid => bank_response_valid,
      response_ready => '1',
      found_o => bank_found,
      overflow_o => bank_overflow,
      membrane_o => bank_membrane,
      adaptation_age_o => bank_age,
      adaptation_amplitude_o => bank_amplitude,
      last_bin_tag_o => bank_last_bin_tag,
      live_entry_count_o => live_entry_count_o
    );

  updater : entity work.plif_update
    generic map (
      MEM_WIDTH => MEM_WIDTH,
      CURRENT_WIDTH => CURRENT_WIDTH,
      BETA_WIDTH => BETA_WIDTH,
      BETA_FRAC_BITS => BETA_FRAC_BITS,
      DELTA_WIDTH => BIN_TAG_WIDTH
    )
    port map (
      clk => clk,
      reset => reset,
      in_valid => plif_in_valid,
      in_ready => plif_in_ready,
      membrane_i => stored_membrane_reg,
      current_i => current_reg,
      beta_i => beta_reg,
      threshold_i => threshold_reg,
      elapsed_bins_i => elapsed_bins_reg,
      out_valid => plif_out_valid,
      out_ready => plif_out_ready,
      candidate_o => plif_candidate,
      membrane_o => plif_membrane,
      spike_o => plif_spike
    );

  sequence_lane : process (clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        lane_state_reg <= idle;
        overflow_reg <= '0';
        result_spike_reg <= '0';
      else
        case lane_state_reg is
          when idle =>
            overflow_reg <= '0';
            result_spike_reg <= '0';
            if in_valid = '1' then
              address_reg <= address_i;
              current_reg <= current_i;
              beta_reg <= beta_i;
              threshold_reg <= threshold_i;
              current_bin_tag_reg <= current_bin_tag_i;
              lane_state_reg <= bank_read_issue;
            end if;

          when bank_read_issue =>
            if bank_request_ready = '1' then
              lane_state_reg <= bank_read_wait;
            end if;

          when bank_read_wait =>
            if bank_response_valid = '1' then
              stored_membrane_reg <= bank_membrane;
              stored_age_reg <= bank_age;
              stored_amp_reg <= bank_amplitude;
              if bank_found = '1' then
                elapsed_bins_reg <= current_bin_tag_reg - bank_last_bin_tag;
              else
                elapsed_bins_reg <= to_unsigned(1, BIN_TAG_WIDTH);
              end if;
              lane_state_reg <= plif_issue;
            end if;

          when plif_issue =>
            if plif_in_ready = '1' then
              lane_state_reg <= plif_wait;
            end if;

          when plif_wait =>
            if plif_out_valid = '1' then
              candidate_reg <= plif_candidate;
              result_membrane_reg <= plif_membrane;
              result_spike_reg <= plif_spike;
              lane_state_reg <= bank_write_issue;
            end if;

          when bank_write_issue =>
            if bank_request_ready = '1' then
              lane_state_reg <= bank_write_wait;
            end if;

          when bank_write_wait =>
            if bank_response_valid = '1' then
              overflow_reg <= bank_overflow;
              lane_state_reg <= hold_result;
            end if;

          when hold_result =>
            if out_ready = '1' then
              lane_state_reg <= idle;
            end if;
        end case;
      end if;
    end if;
  end process;
end architecture;
