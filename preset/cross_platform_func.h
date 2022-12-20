#ifndef PRESET_CROSS_PLATFORM_FUNC_H
#define PRESET_CROSS_PLATFORM_FUNC_H

#include <string>
#include <vector>

namespace occ {
  class HostInfo;
}

std::string getErrorMessage(unsigned long error);

int getHostInfo(occ::HostInfo& info);

int enumUserName(std::vector<std::string>& users);

int setUserPassword(const std::string& userName, const std::string& password);

#endif  // PRESET_CROSS_PLATFORM_FUNC_H
