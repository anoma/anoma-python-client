import asyncio
import json
import base64

from anoma_client import AnomaAPI

intents = []


def solvable(intent_list):
    solvable_set = set()
    for i, intent in enumerate(intent_list):
        for j, other_intent in enumerate(intent_list):
            if i != j and i < j:
                want_give_match = not intent['wants'].isdisjoint(other_intent['gives'])
                give_want_match = not intent['gives'].isdisjoint(other_intent['wants'])

                if want_give_match and give_want_match:
                    solvable_set.add((intent['intent'], other_intent['intent']))
    return solvable_set


def __on_event(client, message):
    global intents
    """
    I handle all incoming events from the websocket.

    :param message: The message coming in over the websocket.
    """
    message = json.loads(message)
    # if an intent was added, attempt a solve.
    if 'source_module' in message and message['source_module'] == 'Elixir.Anoma.Node.Intents.IntentPool':
        intent = message['body']['body']['intent']
        jammed_intent = intent['jammed']

        # inspect the actions and pick out what kinds they want
        actions = intent['actions']

        wanted_kinds = []
        given_kinds = []

        # consumed and created resources as tupled of kind and quantity
        consumed_resources = []
        created_resources = []

        for action in actions:
            consumed_resources.extend(action['consumed_resources'])
            created_resources.extend(action['created_resources'])
            for consumed in action['consumed_resources']:
                given_kinds.append((consumed['label'], consumed['quantity']))

            for created in action['created_resources']:
                wanted_kinds.append((created['label'], created['quantity']))

        # the key of the intent is the resources it wants and the resources it gives.
        intent = {'wants': set(wanted_kinds), 'gives': set(given_kinds), 'intent': jammed_intent}
        intents.append(intent)

        are_solvable = solvable(intents)

        if len(are_solvable) > 0:
            for (x, y) in iter(are_solvable):
                composed = client.compose([base64.b64decode(x), base64.b64decode(y)])
                tx = base64.b64decode(composed['transaction'])
                if client.verify(tx):
                    client.add_transaction(tx, "transparent_resource", wrap=True)

        # check if there are intents we can solve
        # potential_solves = [k for k, v in type_dict.items() if len(v) > 1]
        return
    else:
        print(f"message ignored: {message}")
        return


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
    client.subscribe("*", lambda event: __on_event(client,
                                                   event))  # solver = Solver(client)  #  # # add an intent  # with open("nock/intent.bin", "rb") as intent_bin:  #     intent = intent_bin.read()  #  # result = client.post_intent(intent)  # print(result)  #  # # list the intents  # intents = client.get_intents()  # print(intents)  #  # # add a transaction to the mempool  # with open("nock/tx.bin", "rb") as transaction_bin:  #     transaction = transaction_bin.read()  #     result = client.add_transaction(transaction, "transparent_resource")  #     print(result)  #  # # add a broken transaction to the mempool  # result = client.add_transaction(b'', "transparent_resource")  # print(result)  #  # # prove something  # with open("nock/CellHint.nockma", "rb") as nock_bin:  #     cell_hint = nock_bin.read()  #  #     # the noun 3 in binary representation  #     # the endpoint expects base64 encoded jammed nouns  #     # and returns base64 encoded jammed nouns.  #     #  #     # we want to give 3 as an argument.  #     #  #     # iex> 3 |> Noun.Jam.jam() |> Base.encode64()  #     # "aA=="  #     inputs = [base64.b64decode("aA==")]  #     result = client.run(cell_hint, inputs)  #     print(result)  #  # # run without arguments  # # the endpoint expects base64 encoded jammed nouns  # # and returns base64 encoded jammed nouns.  # #  # # we expect 0 as a result.  # #  # # iex> 0 |> Noun.Jam.jam() |> Base.encode64()  # # "Ag=="  # # base64.b64decode("Ag==")  # # b'\x02'  # with open("nock/Squared.nockma", "rb") as nock_bin:  #     cell_hint = nock_bin.read()  #     inputs = []  #     result = client.run(cell_hint, inputs)  #     print(result)  #  # # run with arguments  # # the endpoint expects base64 encoded jammed nouns  # # and returns base64 encoded jammed nouns.  # #  # # we expect 0 as a result.  # #  # # iex> 0 |> Noun.Jam.jam() |> Base.encode64()  # # "Ag=="  # # base64.b64decode("Ag==")  # # b'\x02'  # with open("nock/Squared.nockma", "rb") as nock_bin:  #     cell_hint = nock_bin.read()  #     inputs = [base64.b64decode("aA==")]  #     result = client.run(cell_hint, inputs)  #     # the result is supposed to be 9  #     # iex(1)> 9 |> Noun.Jam.jam() |> Base.encode64()  #     # "kAQ="  #     # base64.b64decode("kAQ=")  #     # b'\x90\x04'  #     print(result)  #  # # compose two valid transactions  # # these are two empty transactions and they compose trivially  # intent = base64.b64decode("mQI=")  # result = client.compose([intent, intent])  # print(result)  #  # # verify a valid transaction  # intent = base64.b64decode("mQI=")  # result = client.verify(intent)  # print(result)


# Example usage
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
