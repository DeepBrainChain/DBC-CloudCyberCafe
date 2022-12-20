#include "cross_platform_func.h"

#include <algorithm>
#include <utmpx.h>
#include <string.h>
#include <glib.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>

#include "config.h"
#include "preset_types.h"
#include "cross_util.h"

// #ifndef CONFIG_HAS_ENVIRON
#ifdef __APPLE__
#include <crt_externs.h>
#define environ (*_NSGetEnviron())
#else
extern char **environ;
#endif
// #endif

using namespace occ;

namespace {

/* TODO: use this in place of all post-fork() fclose(std*) callers */
void reopen_fd_to_null(int fd) {
  int nullfd;

  nullfd = open("/dev/null", O_RDWR);
  if (nullfd < 0) {
    return;
  }

  dup2(nullfd, fd);

  if (nullfd != fd) {
    close(nullfd);
  }
}

/*
 * A variant of write(2) which handles partial write.
 *
 * Return the number of bytes transferred.
 * Set errno if fewer than `count' bytes are written.
 *
 * This function don't work with non-blocking fd's.
 * Any of the possibilities with non-blocking fd's is bad:
 *   - return a short write (then name is wrong)
 *   - busy wait adding (errno == EAGAIN) to the loop
 */
size_t write_full(int fd, const void *buf, size_t count) {
  size_t ret = 0;
  size_t total = 0;
  while (count) {
    ret = write(fd, buf, count);
    if (ret < 0) {
      if (errno == EINTR)
        continue;
      break;
    }
    count -= ret;
    buf += ret;
    total += ret;
  }
  return total;
}

int wait_child(pid_t pid, int *status) {
  pid_t rpid;
  *status = 0;

  do {
    rpid = waitpid(pid, status, 0);
  } while (rpid == -1 && errno == EINTR);

  if (rpid == -1) {
    // error_setg_errno(errp, errno, "failed to wait for child (pid: %d)", pid);
    return rpid;
  }

  g_assert(rpid == pid);
  return rpid;
}

}

std::string run_shell(const std::string& cmd, const char* modes = "r") {
  if (cmd.empty()) return "";

  std::string ret;
  std::string strcmd = cmd + " 2>&1";
  FILE * fp = nullptr;
  char buffer[1024] = {0};
  fp = popen(strcmd.c_str(), modes);
  if (fp != nullptr) {
    while(fgets(buffer, sizeof(buffer), fp)) {
      ret += std::string(buffer);
    }
    pclose(fp);
  } else {
    ret = std::string("run_shell failed! ") + strcmd + std::string(" ") + std::to_string(errno) + ":" + strerror(errno);
  }

  return rtrim(ret, '\n');
}

std::string getErrorMessage(unsigned long error) {
  std::string msg = "unknowned error";
  return msg;
}

int getHostInfo(HostInfo& info) {
  std::vector<std::string> users;
  enumUserName(users);
  if (std::find(users.begin(), users.end(), GLOBAL_USERNAME) != users.end())
    info.__set_hostName(GLOBAL_USERNAME);
  return 0;
}

int enumUserName(std::vector<std::string>& users) {
  struct utmpx* ut = NULL;
  while ((ut = getutxent()) != NULL) {
    if (ut->ut_type != USER_PROCESS) continue;
    time_t tt = (time_t)(ut->ut_tv.tv_sec);
    tt += ((double)(ut->ut_tv.tv_usec) / 1000000);
    struct tm btm = {0};
    localtime_r(&tt, &btm);
    char buf[256] = {0};
    strftime(buf, sizeof(char) * 256, "%Y-%m-%d %H:%M:%S", &btm);
    printf("%-12s%-12s %s %s\n", ut->ut_user, ut->ut_line, buf, ut->ut_host);
    users.push_back(ut->ut_user);
  }
  endutxent();
  return 0;
}

int setUserPassword(const std::string& userName, const std::string& password) {
  int ret = 1;
  int datafd[2] = { -1, -1 };
  pid_t pid;
  int status;
  std::string chpasswddata = g_strdup_printf("%s:%s\n", userName.c_str(), password.c_str());
  size_t chpasswdlen = chpasswddata.length();
  char* passwd_path = g_find_program_in_path("chpasswd");
  if (!passwd_path) {
    printf("cannot find 'passwd' program in PATH\n");
    goto end;
  }
  if (pipe(datafd) < 0) {
    printf("cannot create pipe FDs\n");
    goto end;
  }
  pid = fork();
  if (pid == 0) {
    close(datafd[1]);
    setsid();
    dup2(datafd[0], 0);
    reopen_fd_to_null(1);
    reopen_fd_to_null(2);
    execle(passwd_path, "chpasswd", NULL, environ);
  } else if (pid < 0) {
    printf("failed to create child process\n");
    goto end;
  }
  close(datafd[0]);
  datafd[0] = -1;

  if (write_full(datafd[1], chpasswddata.c_str(), chpasswdlen) != chpasswdlen) {
    printf("cannot write new account password\n");
    goto end;
  }
  close(datafd[1]);
  datafd[1] = -1;

  if (wait_child(pid, &status) == -1) {
    printf("Error when wait child process: %d - %s\n", errno, strerror(errno));
    goto end;
  }

  if (!WIFEXITED(status)) {
    printf("child process has terminated abnormally\n");
    goto end;
  }

  if (WEXITSTATUS(status)) {
    printf("child process has failed to set user password\n");
    goto end;
  }

  ret = 0;
end:
  g_free(passwd_path);
  if (datafd[0] != -1)
    close(datafd[0]);
  if (datafd[1] != -1)
    close(datafd[1]);
  return ret;
}
