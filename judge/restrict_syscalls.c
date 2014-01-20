#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <sys/reg.h>
#include <stdbool.h>
#include <assert.h>

#ifdef __x86_64__
#define SC_NUMBER  (8 * ORIG_RAX)
#define SC_RETCODE (8 * RAX)
#else
#define SC_NUMBER  (4 * ORIG_EAX)
#define SC_RETCODE (4 * EAX)
#endif

static void child(int _, char** argv)
{
	/* Request tracing by parent: */
	ptrace(PTRACE_TRACEME, 0, NULL, NULL);

	/* Stop before doing anything, giving parent a chance to catch the exec: */
	kill(getpid(), SIGSTOP);

	/* Now exec: */
//	execl("/bin/echo", "echo", "lol", NULL);
	execvp(argv[1], argv+1);
}

const int allowed_syscalls[] = {
	0,1,2,3,4,5,6,7,8,9,10,11,12,21,59,158,231,

	// python2
	218,273,13,14,97,16,89,257,78,79,107,102,108,104,87,

	// gcc
	160,39,58,61,

	// java
	202,56,
};
bool is_allowed_syscall[1024];

static void parent(pid_t child_pid)
{
	int status;
	long sc_number;//, sc_retcode;
	bool exec_done = 0;

	while (1)
	{
		/* Wait for child status to change: */
		wait(&status);

		if (WIFEXITED(status)) {
//			printf("Child exit with status %d\n", WEXITSTATUS(status));
			exit(WEXITSTATUS(status));
		}
		if (WIFSIGNALED(status)) {
			fprintf(stderr, "Child exit due to signal %d\n", WTERMSIG(status));
			exit(0);
		}
		if (!WIFSTOPPED(status)) {
			fprintf(stderr, "wait() returned unhandled status 0x%x\n", status);
			exit(0);
		}
		if (WSTOPSIG(status) == SIGTRAP) {
			/* Note that there are *three* reasons why the child might stop
			 * with SIGTRAP:
			 *  1) syscall entry
			 *  2) syscall exit
			 *  3) child calls exec
			 */
			siginfo_t info;
			ptrace(PTRACE_GETSIGINFO, child_pid, 0, &info);
			if (info.si_code != SIGTRAP) {
				if (exec_done) {
					fprintf(stderr, "CHILD PERFORMED EXEC\n");
					kill(child_pid, SIGKILL);
					abort();
				} else {
					exec_done = 1;
				}
			} else {
				sc_number = ptrace(PTRACE_PEEKUSER, child_pid, SC_NUMBER, NULL);
//				sc_retcode = ptrace(PTRACE_PEEKUSER, child_pid, SC_RETCODE, NULL);
//				printf("SIGTRAP: syscall %ld, rc = %ld\n", sc_number, sc_retcode);
				if (sc_number<0 || sc_number>512 || !is_allowed_syscall[sc_number]) {
					fprintf(stderr, "BLOCKED SYSCALL %ld\n", sc_number);
					kill(child_pid, SIGKILL);
					abort();
				}
			}
		} else {
			if (WSTOPSIG(status) != 19) {
				fprintf(stderr, "Child stopped due to signal %d\n", WSTOPSIG(status));
				exit(1);
			}
		}
//		fflush(stdout);

		/* Resume child, requesting that it stops again on syscall enter/exit
		 * (in addition to any other reason why it might stop):
		 */
		ptrace(PTRACE_SYSCALL, child_pid, NULL, NULL);
	}
}

int main(int argc, char** argv)
{
	assert(argc>1);
	for(int i=0; i<sizeof(allowed_syscalls)/sizeof(allowed_syscalls[0]); ++i) {
		is_allowed_syscall[allowed_syscalls[i]] = 1;
	}
	pid_t pid = fork();

	if (pid == 0)
		child(argc, argv);
	else
		parent(pid);

	return 0;
}
