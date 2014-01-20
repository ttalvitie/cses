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
#include "seccomp-bpf.h"

#ifdef __x86_64__
#define SC_NUMBER  (8 * ORIG_RAX)
#define SC_RETCODE (8 * RAX)
#else
#define SC_NUMBER  (4 * ORIG_EAX)
#define SC_RETCODE (4 * EAX)
#endif

static void set_filters() {
	struct sock_filter filter[] = {
		VALIDATE_ARCHITECTURE,
		EXAMINE_SYSCALL,
		ALLOW_SYSCALL(rt_sigreturn),
		ALLOW_SYSCALL(exit_group),
		ALLOW_SYSCALL(exit),
		ALLOW_SYSCALL(read),
		ALLOW_SYSCALL(write),
		ALLOW_SYSCALL(fstat),
		ALLOW_SYSCALL(mmap),
		ALLOW_SYSCALL(rt_sigaction),
		ALLOW_SYSCALL(rt_sigprocmask),
		ALLOW_SYSCALL(clone),
		ALLOW_SYSCALL(execve),
		ALLOW(20),
		ALLOW(12),
		ALLOW(21),
		ALLOW(2),
		ALLOW(4),
		ALLOW(3),
		ALLOW(10),
		ALLOW(158),
		ALLOW(11),
		ALLOW(61),
		ALLOW(16),
		KILL_PROCESS,
	};

	struct sock_fprog prog = {
		sizeof(filter) / sizeof(filter[0]),
		filter
	};
	int ret=0;
	ret = prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
	assert(!ret);
	ret = prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
	assert(!ret);
}


static void child(int _, char** argv)
{
	/* Request tracing by parent: */
	ptrace(PTRACE_TRACEME, 0, NULL, NULL);

	/* Stop before doing anything, giving parent a chance to catch the exec: */
	kill(getpid(), SIGSTOP);

	set_filters();

	/* Now exec: */
//	execl("/bin/echo", "echo", "lol", NULL);
	execvp(argv[1], argv+1);
}

#if 0
const int allowed_syscalls[] = {
	0,1,2,3,4,5,6,7,8,9,10,11,12,21,59,158,231,
	// sync_with_stdio(0)
	20,

	// python2
	218,273,13,14,97,16,89,257,78,79,107,102,108,104,87,

	// gcc
	160,39,58,61,

	// java
	202,56,
};
bool is_allowed_syscall[1024];
#endif

static void parent(pid_t child_pid)
{
	int status;
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
#if 0
				sc_number = ptrace(PTRACE_PEEKUSER, child_pid, SC_NUMBER, NULL);
//				sc_retcode = ptrace(PTRACE_PEEKUSER, child_pid, SC_RETCODE, NULL);
//				printf("SIGTRAP: syscall %ld, rc = %ld\n", sc_number, sc_retcode);
				if (sc_number<0 || sc_number>512 || !is_allowed_syscall[sc_number]) {
					fprintf(stderr, "BLOCKED SYSCALL %ld\n", sc_number);
					kill(child_pid, SIGKILL);
					abort();
				}
#endif
			}
		} else if (WSTOPSIG(status) == 31) {
			long sc_number = ptrace(PTRACE_PEEKUSER, child_pid, SC_NUMBER, NULL);
			fprintf(stderr, "BLOCKED SYSCALL %ld\n", sc_number);
			kill(child_pid, SIGKILL);
			exit(1);
		} else {
			if (WSTOPSIG(status) != 19) {
				fprintf(stderr, "Child stopped due to signal %d\n", WSTOPSIG(status));
				kill(child_pid, SIGKILL);
				exit(1);
			}
		}
//		fflush(stdout);

		/* Resume child, requesting that it stops again on syscall enter/exit
		 * (in addition to any other reason why it might stop):
		 */
//		ptrace(PTRACE_SYSCALL, child_pid, NULL, NULL);
		ptrace(PTRACE_CONT, child_pid, NULL, NULL);
	}
}

int main(int argc, char** argv)
{
	assert(argc>1);
#if 0
	for(int i=0; i<sizeof(allowed_syscalls)/sizeof(allowed_syscalls[0]); ++i) {
		is_allowed_syscall[allowed_syscalls[i]] = 1;
	}
#endif
	pid_t pid = fork();

	if (pid == 0)
		child(argc, argv);
	else
		parent(pid);

	return 0;
}
