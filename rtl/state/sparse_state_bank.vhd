library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Lossless zero-default state bank for 5-ms binned touched-neuron execution.
--
-- A missing address represents the exact reset state. Live entries store a compact
-- last-bin tag so the PLIF lane can apply beta**delta_bins lazily when a neuron is
-- touched again; no microsecond timestamp is stored.
-- Live writes update an existing entry or allocate an invalid way.  Dead writes
-- reclaim an exact matching entry.  A full set never evicts state silently:
-- overflow_o is asserted and the table remains unchanged.
entity sparse_state_bank is
  generic (
    ADDRESS_WIDTH    : positive := 28;
    MEMBRANE_WIDTH   : positive := 16;
    ADAPTATION_WIDTH : positive := 16;
    BIN_TAG_WIDTH     : positive := 24;
    SET_COUNT        : positive := 8;
    WAY_COUNT        : positive := 2;
    COUNT_WIDTH      : positive := 16
  );
  port (
    clk                    : in  std_logic;
    reset                  : in  std_logic;
    request_valid          : in  std_logic;
    request_ready          : out std_logic;
    write_enable           : in  std_logic;
    address_i              : in  unsigned(ADDRESS_WIDTH - 1 downto 0);
    state_live_i           : in  std_logic;
    membrane_i             : in  signed(MEMBRANE_WIDTH - 1 downto 0);
    adaptation_age_i       : in  signed(ADAPTATION_WIDTH - 1 downto 0);
    adaptation_amplitude_i : in  signed(ADAPTATION_WIDTH - 1 downto 0);
    last_bin_tag_i          : in  unsigned(BIN_TAG_WIDTH - 1 downto 0);
    response_valid         : out std_logic;
    response_ready         : in  std_logic;
    found_o                : out std_logic;
    overflow_o             : out std_logic;
    membrane_o             : out signed(MEMBRANE_WIDTH - 1 downto 0);
    adaptation_age_o       : out signed(ADAPTATION_WIDTH - 1 downto 0);
    adaptation_amplitude_o : out signed(ADAPTATION_WIDTH - 1 downto 0);
    last_bin_tag_o          : out unsigned(BIN_TAG_WIDTH - 1 downto 0);
    live_entry_count_o     : out unsigned(COUNT_WIDTH - 1 downto 0)
  );
end entity;

architecture rtl of sparse_state_bank is
  type valid_array_t is array (0 to SET_COUNT - 1, 0 to WAY_COUNT - 1) of std_logic;
  type tag_array_t is array (0 to SET_COUNT - 1, 0 to WAY_COUNT - 1) of
    unsigned(ADDRESS_WIDTH - 1 downto 0);
  type membrane_array_t is array (0 to SET_COUNT - 1, 0 to WAY_COUNT - 1) of
    signed(MEMBRANE_WIDTH - 1 downto 0);
  type adaptation_array_t is array (0 to SET_COUNT - 1, 0 to WAY_COUNT - 1) of
    signed(ADAPTATION_WIDTH - 1 downto 0);
  type bin_tag_array_t is array (0 to SET_COUNT - 1, 0 to WAY_COUNT - 1) of
    unsigned(BIN_TAG_WIDTH - 1 downto 0);

  signal valid_memory     : valid_array_t := (others => (others => '0'));
  signal tag_memory       : tag_array_t;
  signal membrane_memory  : membrane_array_t;
  signal age_memory       : adaptation_array_t;
  signal amplitude_memory : adaptation_array_t;
  signal last_bin_memory   : bin_tag_array_t;

  signal response_valid_reg : std_logic := '0';
  signal found_reg          : std_logic := '0';
  signal overflow_reg       : std_logic := '0';
  signal membrane_reg       : signed(MEMBRANE_WIDTH - 1 downto 0) := (others => '0');
  signal age_reg            : signed(ADAPTATION_WIDTH - 1 downto 0) := (others => '0');
  signal amplitude_reg      : signed(ADAPTATION_WIDTH - 1 downto 0) := (others => '0');
  signal last_bin_reg       : unsigned(BIN_TAG_WIDTH - 1 downto 0) := (others => '0');
  signal live_count_reg     : unsigned(COUNT_WIDTH - 1 downto 0) := (others => '0');

  function is_power_of_two(value : positive) return boolean is
    variable remaining : natural := value;
  begin
    while remaining > 1 loop
      if remaining mod 2 /= 0 then
        return false;
      end if;
      remaining := remaining / 2;
    end loop;
    return true;
  end function;
begin
  assert is_power_of_two(SET_COUNT)
    report "SET_COUNT must be a power of two"
    severity failure;
  assert ADDRESS_WIDTH <= 30
    report "ADDRESS_WIDTH must fit the VHDL integer range"
    severity failure;
  assert (2 ** COUNT_WIDTH) > SET_COUNT * WAY_COUNT
    report "COUNT_WIDTH cannot represent the sparse-bank capacity"
    severity failure;

  request_ready <= not response_valid_reg or response_ready;
  response_valid <= response_valid_reg;
  found_o <= found_reg;
  overflow_o <= overflow_reg;
  membrane_o <= membrane_reg;
  adaptation_age_o <= age_reg;
  adaptation_amplitude_o <= amplitude_reg;
  last_bin_tag_o <= last_bin_reg;
  live_entry_count_o <= live_count_reg;

  access_bank : process (clk)
    variable set_index : natural range 0 to SET_COUNT - 1;
    variable hit_way   : integer range -1 to WAY_COUNT - 1;
    variable free_way  : integer range -1 to WAY_COUNT - 1;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        valid_memory <= (others => (others => '0'));
        response_valid_reg <= '0';
        found_reg <= '0';
        overflow_reg <= '0';
        live_count_reg <= (others => '0');
      elsif (not response_valid_reg or response_ready) = '1' then
        response_valid_reg <= request_valid;
        found_reg <= '0';
        overflow_reg <= '0';
        membrane_reg <= (others => '0');
        age_reg <= (others => '0');
        amplitude_reg <= (others => '0');
        last_bin_reg <= (others => '0');

        if request_valid = '1' then
          set_index := to_integer(address_i) mod SET_COUNT;
          hit_way := -1;
          free_way := -1;
          for way in 0 to WAY_COUNT - 1 loop
            if valid_memory(set_index, way) = '1'
              and tag_memory(set_index, way) = address_i then
              hit_way := way;
            elsif valid_memory(set_index, way) = '0' and free_way = -1 then
              free_way := way;
            end if;
          end loop;

          if hit_way >= 0 then
            found_reg <= '1';
            membrane_reg <= membrane_memory(set_index, hit_way);
            age_reg <= age_memory(set_index, hit_way);
            amplitude_reg <= amplitude_memory(set_index, hit_way);
            last_bin_reg <= last_bin_memory(set_index, hit_way);
          end if;

          if write_enable = '1' then
            if state_live_i = '0' then
              if hit_way >= 0 then
                valid_memory(set_index, hit_way) <= '0';
                live_count_reg <= live_count_reg - 1;
              end if;
            elsif hit_way >= 0 then
              membrane_memory(set_index, hit_way) <= membrane_i;
              age_memory(set_index, hit_way) <= adaptation_age_i;
              amplitude_memory(set_index, hit_way) <= adaptation_amplitude_i;
              last_bin_memory(set_index, hit_way) <= last_bin_tag_i;
            elsif free_way >= 0 then
              valid_memory(set_index, free_way) <= '1';
              tag_memory(set_index, free_way) <= address_i;
              membrane_memory(set_index, free_way) <= membrane_i;
              age_memory(set_index, free_way) <= adaptation_age_i;
              amplitude_memory(set_index, free_way) <= adaptation_amplitude_i;
              last_bin_memory(set_index, free_way) <= last_bin_tag_i;
              live_count_reg <= live_count_reg + 1;
            else
              overflow_reg <= '1';
            end if;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
