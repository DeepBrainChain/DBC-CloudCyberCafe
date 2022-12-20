#ifndef PRESET_HANDLER_H
#define PRESET_HANDLER_H

#include "Preset.h"

class PresetHandler : virtual public occ::PresetIf {
public:
  PresetHandler();

  void ping(std::string& _return);

  void handleMessage(occ::ResultStruct& _return, const occ::Message& msg);

protected:
  occ::HostInfo info_;

};

#endif  // PRESET_HANDLER_H
