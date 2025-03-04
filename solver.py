import base64
import json

from more_itertools import powerset_of_sets


class Solver:
    def __init__(self, client):
        self.unsolved = set([])
        self.client = client
        client.subscribe("tx_events", lambda message: self.__on_event(message))

    def __on_event(self, message):
        """
        I handle all incoming events from the websocket.

        :param message: The message coming in over the websocket.
        """
        message = json.loads(message)
        # if an intent was added, attempt a solve.
        if message["event"]["name"] == 'Elixir.Anoma.Node.Events.IntentAddSuccess':
            decoded_intent = base64.b64decode(message["event"]["intent"])
            self.unsolved.add(decoded_intent)
            self.solve()
        else:
            print(f"message ignored: {message}")

    def solve(self):
        """I attempt to solve a subset of the unsolved intents."""
        subsets = powerset_of_sets(self.unsolved)
        for subset in subsets:
            # compose the transactions in the subset
            # if they are composed submit them and mark them as solved.
            # if they did not compose, skip this subset.
            result = self.client.compose(list(subset))
            if "error" in result:
                print("failed to solve subset, skipping")
            else:
                composed = base64.b64decode(result["transaction"])
                # remove the solved intents from the unsolved set
                for intent in subset:
                    self.unsolved.remove(intent)

                # submit the composed intent to the mempool
                result = self.client.add_transaction(composed)
                print(result)
