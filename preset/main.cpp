#include <iostream>
#include <string>

#include <boost/program_options.hpp>

#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/server/TSimpleServer.h>
#include <thrift/transport/TServerSocket.h>
#include <thrift/transport/TBufferTransports.h>

#include "config.h"
#include "preset_handler.h"

namespace bpo = boost::program_options;

using namespace ::apache::thrift;
using namespace ::apache::thrift::protocol;
using namespace ::apache::thrift::transport;
using namespace ::apache::thrift::server;

using namespace occ;

int main(int argc, char* argv[]) {
  int port = 9090;
  bpo::options_description opts("preset " PRESET_VERSION " command options");
  opts.add_options()
    ("name,n", bpo::value<std::string>(), "param name")
    ("port,p", bpo::value<int>(), "param port")
    ("version,v", "print version and exit")
    ("help,h", "display help and exit");
  bpo::variables_map vm;
  try {
    bpo::store(bpo::parse_command_line(argc, argv, opts), vm);
    bpo::notify(vm);

    // std::cout << "param count " << vm.size() << std::endl;
    if (vm.count("help") > 0) {
      std::cout << opts;
      return 0;
    }
    if (vm.count("version") > 0) {
      std::cout << "preset " << PRESET_VERSION << std::endl;
      return 0;
    }
    if (vm.count("name") > 0) {
      std::cout << "input name=" << vm["name"].as<std::string>() << std::endl;
    }
    if (vm.count("port") > 0) {
      // std::cout << "input port=" << vm["port"].as<int>() << std::endl;
      port = vm["port"].as<int>();
    }

    ::std::shared_ptr<PresetHandler> handler(new PresetHandler());
    ::std::shared_ptr<TProcessor> processor(new PresetProcessor(handler));
    ::std::shared_ptr<TServerTransport> serverTransport(new TServerSocket(port));
    ::std::shared_ptr<TTransportFactory> transportFactory(new TBufferedTransportFactory());
    ::std::shared_ptr<TProtocolFactory> protocolFactory(new TBinaryProtocolFactory());

    TSimpleServer server(processor, serverTransport, transportFactory, protocolFactory);
    printf("Starting cpp server...\n");
    server.serve();
    printf("done!\n");
    return 0;
  }
  catch (const std::exception &e) {
    std::cout << "invalid command option " << e.what() << std::endl;
    std::cout << opts;
    return -1;
  }
  return 0;
}
