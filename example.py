import asyncio
import base64
from anoma_client import AnomaAPI
from solver import Solver




async def main():
    """
    Run an example of the client.

    Start an Elixir node as follows.
    ```
    iex> node = Anoma.Node.Examples.ENode.start_node(node_id: "beef")
    iex> {:ok, client} = Anoma.Client.connect("localhost", 40051, "beef")
    ```
    """
    client = AnomaAPI(host="localhost", port=4000)
    solver = Solver(client)

    # add an intent
    with open("nock/intent.bin", "rb") as intent_bin:
        intent = intent_bin.read()

    result = client.post_intent(intent)
    print(result)

    # list the intents
    intents = client.get_intents()
    print(intents)

    # add a transaction to the mempool
    with open("nock/tx.bin", "rb") as transaction_bin:
        transaction = transaction_bin.read()

    result = client.add_transaction(b'')
    print(result)

    # add a broken transaction to the mempool
    result = client.add_transaction(b'')
    print(result)

    # prove something
    with open("nock/CellHint.nockma", "rb") as nock_bin:
        cell_hint = nock_bin.read()

    # the noun 3 in binary representation
    # the endpoint expects base64 encoded jammed nouns
    # and returns base64 encoded jammed nouns.
    #
    # we want to give 3 as an argument.
    #
    # iex> 3 |> Noun.Jam.jam() |> Base.encode64()
    # "aA=="
    inputs = [base64.b64decode("aA==")]
    result = client.run(cell_hint, inputs)
    print(result)

    # run without arguments
    # the endpoint expects base64 encoded jammed nouns
    # and returns base64 encoded jammed nouns.
    #
    # we expect 0 as a result.
    #
    # iex> 0 |> Noun.Jam.jam() |> Base.encode64()
    # "Ag=="
    # base64.b64decode("Ag==")
    # b'\x02'
    with open("nock/Squared.nockma", "rb") as nock_bin:
        cell_hint = nock_bin.read()

    inputs = []
    result = client.run(cell_hint, inputs)
    print(result)

    # run with arguments
    # the endpoint expects base64 encoded jammed nouns
    # and returns base64 encoded jammed nouns.
    #
    # we expect 0 as a result.
    #
    # iex> 0 |> Noun.Jam.jam() |> Base.encode64()
    # "Ag=="
    # base64.b64decode("Ag==")
    # b'\x02'
    with open("nock/Squared.nockma", "rb") as nock_bin:
        cell_hint = nock_bin.read()

    inputs = [base64.b64decode("aA==")]
    result = client.run(cell_hint, inputs)
    # the result is supposed to be 9
    # iex(1)> 9 |> Noun.Jam.jam() |> Base.encode64()
    # "kAQ="
    # base64.b64decode("kAQ=")
    # b'\x90\x04'
    print(result)


    # compose two valid transactions
    # these are two empty transactions and they compose trivially
    intent = base64.b64decode("mSk=")
    result = client.compose([intent, intent])
    print(result)

    # verify a valid transaction
    intent = base64.b64decode("mSk=")
    result = client.verify(intent)
    print(result)


# Example usage
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
