library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Two-bank event ingress for continuous 5 ms acquisition.
--
-- Camera events are written into one bank while a sealed bank is consumed by
-- actor 0.  Sealing an empty bank is legal because an empty 5 ms interval must
-- still advance recurrent time.  A bank is never overwritten until release_i
-- confirms that the complete end-to-end graph has retired its bin.
entity ping_pong_event_buffer is
  generic (
    DATA_WIDTH  : positive := 32;
    DEPTH       : positive := 1024;
    COUNT_WIDTH : positive := 11
  );
  port (
    clk                  : in  std_logic;
    reset                : in  std_logic;
    capture_valid_i      : in  std_logic;
    capture_ready_o      : out std_logic;
    capture_data_i       : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    seal_i               : in  std_logic;
    seal_ready_o         : out std_logic;
    overflow_o           : out std_logic;
    sealed_valid_o       : out std_logic;
    sealed_ready_i       : in  std_logic;
    sealed_buffer_o      : out std_logic;
    active_valid_o       : out std_logic;
    active_buffer_o      : out std_logic;
    active_event_count_o : out unsigned(COUNT_WIDTH - 1 downto 0);
    event_valid_o        : out std_logic;
    event_ready_i        : in  std_logic;
    event_data_o         : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    event_last_o         : out std_logic;
    release_i            : in  std_logic
  );
end entity;

architecture rtl of ping_pong_event_buffer is
  type memory_t is array (0 to 1, 0 to DEPTH - 1) of
    std_logic_vector(DATA_WIDTH - 1 downto 0);
  type count_array_t is array (0 to 1) of natural range 0 to DEPTH;

  signal memory            : memory_t;
  signal event_count_reg   : count_array_t := (others => 0);
  signal write_bank_reg    : natural range 0 to 1 := 0;
  signal ready_valid_reg   : std_logic := '0';
  signal ready_bank_reg    : natural range 0 to 1 := 0;
  signal active_valid_reg  : std_logic := '0';
  signal active_bank_reg   : natural range 0 to 1 := 0;
  signal read_index_reg    : natural range 0 to DEPTH := 0;
  signal overflow_reg      : std_logic := '0';
  signal write_bank_free   : std_logic;
begin
  assert (2 ** COUNT_WIDTH) > DEPTH
    report "COUNT_WIDTH cannot represent DEPTH"
    severity failure;

  write_bank_free <= '1' when
    not (ready_valid_reg = '1' and ready_bank_reg = write_bank_reg)
    and not (active_valid_reg = '1' and active_bank_reg = write_bank_reg)
    else '0';

  capture_ready_o <= '1' when
    write_bank_free = '1' and event_count_reg(write_bank_reg) < DEPTH
    else '0';
  -- Only one sealed-but-not-yet-active bin can be queued with two physical banks.
  seal_ready_o <= not ready_valid_reg and write_bank_free;
  overflow_o <= overflow_reg;
  sealed_valid_o <= ready_valid_reg and not active_valid_reg;
  sealed_buffer_o <= '0' when ready_bank_reg = 0 else '1';
  active_valid_o <= active_valid_reg;
  active_buffer_o <= '0' when active_bank_reg = 0 else '1';
  active_event_count_o <= to_unsigned(event_count_reg(active_bank_reg), COUNT_WIDTH);
  event_valid_o <= '1' when
    active_valid_reg = '1' and read_index_reg < event_count_reg(active_bank_reg)
    else '0';
  event_data_o <= memory(active_bank_reg, read_index_reg)
    when active_valid_reg = '1' and read_index_reg < event_count_reg(active_bank_reg)
    else (others => '0');
  event_last_o <= '1' when
    active_valid_reg = '1'
    and event_count_reg(active_bank_reg) > 0
    and read_index_reg = event_count_reg(active_bank_reg) - 1
    else '0';

  manage_buffers : process (clk)
    variable next_bank : natural range 0 to 1;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        event_count_reg <= (others => 0);
        write_bank_reg <= 0;
        ready_valid_reg <= '0';
        ready_bank_reg <= 0;
        active_valid_reg <= '0';
        active_bank_reg <= 0;
        read_index_reg <= 0;
        overflow_reg <= '0';
      else
        overflow_reg <= '0';

        if capture_valid_i = '1' then
          if write_bank_free = '1' and event_count_reg(write_bank_reg) < DEPTH then
            memory(write_bank_reg, event_count_reg(write_bank_reg)) <= capture_data_i;
            event_count_reg(write_bank_reg) <= event_count_reg(write_bank_reg) + 1;
          else
            overflow_reg <= '1';
          end if;
        end if;

        if seal_i = '1' then
          if ready_valid_reg = '0' and write_bank_free = '1' then
            ready_valid_reg <= '1';
            ready_bank_reg <= write_bank_reg;
            next_bank := 1 - write_bank_reg;
            write_bank_reg <= next_bank;
          else
            overflow_reg <= '1';
          end if;
        end if;

        if ready_valid_reg = '1' and active_valid_reg = '0'
          and sealed_ready_i = '1' then
          active_valid_reg <= '1';
          active_bank_reg <= ready_bank_reg;
          read_index_reg <= 0;
          ready_valid_reg <= '0';
        end if;

        if active_valid_reg = '1' and event_ready_i = '1'
          and read_index_reg < event_count_reg(active_bank_reg) then
          read_index_reg <= read_index_reg + 1;
        end if;

        if release_i = '1' then
          if active_valid_reg = '1' then
            event_count_reg(active_bank_reg) <= 0;
            active_valid_reg <= '0';
            read_index_reg <= 0;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
