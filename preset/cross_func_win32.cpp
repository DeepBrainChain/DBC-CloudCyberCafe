#include "cross_platform_func.h"

// #define _CRT_SECURE_NO_WARNINGS
#define WIN32_LEAN_AND_MEAN

#include <Windows.h>
#include <tchar.h>
#include <lm.h>
#include <sddl.h>

#pragma comment(lib, "advapi32.lib")
#pragma comment(lib, "netapi32.lib")

#include "config.h"
#include "preset_types.h"

using namespace occ;

static inline std::wstring string2Wstring(const std::string& str, UINT codePage) {
  std::wstring res;
  int nLen = ::MultiByteToWideChar(codePage, 0, str.c_str(), str.length(), NULL, 0);
  if (nLen <= 0) return res;
  res.resize(nLen);
  nLen = ::MultiByteToWideChar(codePage, 0, str.c_str(), str.length(), &res[0], nLen);
  if (nLen > 0) return res;
  return std::wstring();
}

static inline std::string wstring2String(const std::wstring& wstr, UINT codePage) {
  std::string res;
  int nLen = ::WideCharToMultiByte(codePage, 0, wstr.c_str(), wstr.length(), NULL, 0, NULL, NULL);
  if (nLen <= 0) return res;
  res.resize(nLen);
  nLen = ::WideCharToMultiByte(codePage, 0, wstr.c_str(), wstr.length(), &res[0], nLen, NULL, NULL);
  if (nLen > 0) return res;
  return "";
}

static std::wstring utf8ToUnicode(const std::string& str) {
  return string2Wstring(str, CP_UTF8);
}

static std::string unicodeToUtf8(const std::wstring& wstr) {
  return wstring2String(wstr, CP_UTF8);
}

static inline std::wstring getFormatMessage(DWORD error) {
  std::wstring res;
  HMODULE module = NULL;
  wchar_t* lpMsgBuf = NULL;
  DWORD flags = FORMAT_MESSAGE_ALLOCATE_BUFFER |
    FORMAT_MESSAGE_IGNORE_INSERTS |
    FORMAT_MESSAGE_FROM_SYSTEM;
  if (error >= NERR_BASE && error <= MAX_NERR) {
    module = LoadLibraryExW(L"netmsg.dll", NULL, LOAD_LIBRARY_AS_DATAFILE);
    if (module != NULL) flags |= FORMAT_MESSAGE_FROM_HMODULE;
  }
  DWORD nLen = FormatMessageW(flags, module, error,
    MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPWSTR)&lpMsgBuf, 0, NULL);
  if (nLen > 0) {
    if (nLen >= 2  && lpMsgBuf[nLen - 1] == L'\n' && lpMsgBuf[nLen - 2] == L'\r') {
      lpMsgBuf[nLen - 2] = L'\0';
      res.assign(lpMsgBuf, nLen - 1);
    } else if (nLen >= 1  && lpMsgBuf[nLen - 1] == L'\n') {
      lpMsgBuf[nLen - 1] = L'\0';
      res.assign(lpMsgBuf, nLen);
    } else {
      res.assign((LPCTSTR)lpMsgBuf, nLen);
    }
  }
  if (lpMsgBuf) LocalFree(lpMsgBuf);
  if (module) FreeLibrary(module);
  return res;
}

std::string getErrorMessage(unsigned long error) {
  std::wstring msg = getFormatMessage(error);
  if (msg.empty())
    msg = L"Error message id " + std::to_wstring(error);
  return unicodeToUtf8(msg);
}

int getHostInfo(HostInfo& info) {
  std::vector<std::string> users;
  enumUserName(users);
  if (std::find(users.begin(), users.end(), GLOBAL_USERNAME) != users.end())
    info.__set_hostName(GLOBAL_USERNAME);
  return 0;
}

int enumUserName(std::vector<std::string>& users) {
  LPUSER_INFO_0 pBuf = NULL;
  LPUSER_INFO_0 pTmpBuf;
  DWORD dwLevel = 0;
  DWORD dwPrefMaxLen = MAX_PREFERRED_LENGTH;
  DWORD dwEntriesRead = 0;
  DWORD dwTotalEntries = 0;
  DWORD dwResumeHandle = 0;
  DWORD i;
  DWORD dwTotalCount = 0;
  NET_API_STATUS nStatus;
  do {
    nStatus = NetUserEnum(NULL, dwLevel, FILTER_NORMAL_ACCOUNT, (LPBYTE*)&pBuf,
      dwPrefMaxLen, &dwEntriesRead, &dwTotalEntries, &dwResumeHandle);
    if ((nStatus == NERR_Success)  || (nStatus == ERROR_MORE_DATA)) {
      if ((pTmpBuf = pBuf) != NULL) {
        // Loop through the entries.
        for (i = 0; (i < dwEntriesRead); i++) {
          assert(pTmpBuf != NULL);
          if (pTmpBuf == NULL) {
            printf("An access violation has occurred\n");
            break;
          }
          printf("\t-- %s\n", unicodeToUtf8(pTmpBuf->usri0_name).c_str());
          users.push_back(unicodeToUtf8(pTmpBuf->usri0_name));
          pTmpBuf++;
          dwTotalCount++;
        }
      }
    } else {
      printf("A system error has occurred: %d\n", nStatus);
    }
    if (pBuf != NULL) {
      NetApiBufferFree(pBuf);
      pBuf = NULL;
    }
  } while (nStatus == ERROR_MORE_DATA);
  if (pBuf != NULL)
    NetApiBufferFree(pBuf);
  printf("\nTotal of %d entries enumerated\n", dwTotalCount);
  return 0;
}

int setUserPassword(const std::string& userName, const std::string& password) {
  std::wstring wUserName = utf8ToUnicode(userName);
  std::wstring wPassword = utf8ToUnicode(password);
  USER_INFO_1003 ui;
  NET_API_STATUS nStatus;
  ui.usri1003_password = &wPassword[0];
  nStatus = NetUserSetInfo(NULL, wUserName.c_str(), 1003, (LPBYTE)&ui, NULL);
  if (nStatus == NERR_Success)
    printf("User password %s has been changed\n", userName.c_str());
  else
    printf("A system error has occurred: %d\n", nStatus);
  return nStatus;
}
