# 5: Distributed Computing
This week you need to implement distributed computing via [remote procedure call (RPC)](https://en.wikipedia.org/wiki/Remote_procedure_call), which has similiar interface you get with real robot via PyNaoQi.

The server and client have to be implemented together:
* [ServerAgent](./agent_server.py) provides remote RPC service;
* [ClientAgent](./agent_client.py) requests remote call from server and provides non-blocking capibility.

1. Run ' -m pip install grpcio '

2. Run ' py -m pip install grpcio grpcio-tools ' 

3. Run ' py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. distributed_computing/communication.proto '
