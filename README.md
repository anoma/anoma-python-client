# Anoma Python Client

A reference implementation of a third-party client written in Python.

## Running the client 

1. Create an instance of the Anoma node from [this repository](https://github.com/anoma/anoma).
2. Start the node using the following commands.
   ```iex 
   iex(1)> node = Anoma.Node.Examples.ENode.start_node()
   %Anoma.Node.Examples.ENode{pid: #PID<0.769.0>, node_id: "128809722"}
   iex(2)> {:ok, client} = Anoma.Client.connect("localhost", 50051, "128809722")
   {:ok, %Anoma.Client{pid: #PID<0.753.0>}}
   ```
   The local Anoma client will accept requests on port `4000` by default, and websocket connections on port `3000` by default.
3. Run the Python client.
   
   

