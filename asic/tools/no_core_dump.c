/* WSL piped core handlers may ignore RLIMIT_CORE. Disable dumping after exec. */
#include <sys/prctl.h>
#include <unistd.h>

__attribute__((constructor)) static void disable_core_dump(void) {
    if (prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0) {
        static const char message[] = "Unable to disable synthesis core dumps\n";
        write(STDERR_FILENO, message, sizeof(message) - 1);
        _exit(125);
    }
}
