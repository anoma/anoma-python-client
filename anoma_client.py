import asyncio
import base64

import requests
import websockets
from requests import HTTPError


class AnomaAPI:
    def __init__(self, host, port):
        self.websocket_url = f"ws://{host}:{port}/socket/websocket"
        self.base_url = f"http://{host}:{port}"
        self.websocket = None
        self.on_message = None
        self.task = None

    async def connect_websocket(self):
        """
        I connect to the client's websocket endpoint.
        For each incoming message I will call the on_message function.
        """
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                print("Connected to event stream")
                await self.handle_messages(self.websocket)
        except Exception as e:
            print(f"event stream connection error: {e}")

    async def handle_messages(self, websocket):
        """
        I handle all incomping messages from the websocket.
        If there is a callback installed in on_message, I call it.
        Otherwise, I do nothing.
        """
        async for message in websocket:
            # if a callback was installed, call it.
            if self.on_message is not None:
                self.on_message(message)

    async def stop(self):
        """
        I stop the websocket connection to the client.
        """
        if self.websocket:
            await self.websocket.close()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                print("event stream closed")

    def __do_post(self, path, payload):
        """
        I make a POST request to the client endpoint.

        :param path: path of the endpoint to talk to.
        :param payload: dictionary as json payload.
        :return: dictionary
        """
        try:
            response = requests.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()
        except HTTPError as err:
            response = err.response.json()
            return response

    def __do_get(self, path):
        """
        I make a GET request to the client endpoint.

        :param path: path of the endpoint to talk to.
        :return: dictionary
        """
        try:
            response = requests.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except HTTPError as err:
            response = err.response.json()
            return response

    def get_intents(self) -> [bytes]:
        """
        I call GET /intents and return the list of intents.
        :return: a list of intents in jammed noun format.
        """
        api_result = self.__do_get("/intents")
        return [base64.b64decode(i) for i in api_result["intents"]]

    def post_intent(self, jammed_intent: bytes) -> object:
        """
        I call POST /intents with the provided intent name.
        I return an object that contains the result of this operation.
        :return: an object that contains the result of the operation.
                 `{'error': 'failed to add intent', 'reason': 'invalid nock code'}` for a failed operation.
                 `{'message': 'intent added'}` for a successful operation.
        """
        payload = {"intent": base64.b64encode(jammed_intent).decode("utf-8")}
        api_result = self.__do_post("/intents", payload)
        return api_result

    def run(self, program: bytes, inputs: [bytes]) -> object:
        """
        I call the /nock/run path with the given program and inputs.
        :param program: jammed noun of the program
        :param inputs:  jammed nouns for each input.
        :return: an object that contains the result of the operation, and the hints that were generated during execution.
        """
        inputs = [base64.b64encode(i).decode("utf-8") for i in inputs]
        program = base64.b64encode(program).decode("utf-8")
        payload = {"inputs": inputs, "program": program}

        response = self.__do_post("/nock/run", payload)
        api_result = base64.b64decode(response["result"])
        hints = [base64.b64decode(hint) for hint in response["io"]]
        return {"io": hints, "result": api_result}

    def prove(self, program: bytes, private_inputs: [bytes], public_inputs: [bytes]) -> object:
        """
        I call the /nock/prove path with the given program and inputs.
        :param program: jammed noun of the program
        :param private_inputs:  jammed nouns for each input.
        :param public_inputs:  jammed nouns for each input.
        :return: an object that contains the result of the operation, and the hints that were generated during execution.
        """
        private_inputs = [base64.b64encode(i).decode("utf-8") for i in private_inputs]
        public_inputs = [base64.b64encode(i).decode("utf-8") for i in public_inputs]
        program = base64.b64encode(program).decode("utf-8")

        payload = {"public_inputs": public_inputs, "private_inputs": private_inputs, "program": program}
        response = self.__do_post("/nock/prove", payload)
        api_result = base64.b64decode(response["result"])
        hints = [base64.b64decode(hint) for hint in response["io"]]
        return {"io": hints, "result": api_result}

    def add_transaction(self, transaction: bytes) -> object:
        """
        I call the /mempool/add endpoint to add a transaction to the node's mempool.
        :param transaction: Jammed noun of a transaction.
        :return: an object that contains the result of the operation.
                 `{'error': 'failed to add transaction', 'reason': 'invalid nock code'}` for a failed operation.
                 `{'message': 'transaction added'}` for a successful operation.
        """
        payload = {"transaction": base64.b64encode(transaction).decode("utf-8")}
        api_result = self.__do_post("/mempool/add", payload)
        return api_result

    def subscribe(self, topic: str, on_message) -> object:
        """
        I call the /subscribe endpoint to subscribe to websocket events from the client.

        :param topic: A topic to subscribe to. E.g., `tx_events` or `*`.
        :param on_message: A callback to handle each message. Expects a function that takes a single argument.
        :return:
        """
        payload = {"topic": topic}
        api_result = self.__do_post("/subscribe", payload)
        self.on_message = on_message
        self.task = asyncio.create_task(self.connect_websocket())

        return api_result

    def compose(self, intents: [bytes]) -> bytes:
        """
        I call POST /transactions/compose with the provided list of intents.
        :param intents: A list of jammed nouns that represent intents to be composed.
        :return: An object that contains the result of the operation.
                 `{'transaction': b''}` a  binary representation of the transaction.
                 `{'error': 'failed to compose the transactions. are all transactions valid?', 'reason': reason}` if the composition failed.
        """
        encoded_intents = [base64.b64encode(intent).decode("utf-8") for intent in intents]
        payload = {"transactions": encoded_intents}
        api_result = self.__do_post("/transactions/compose", payload)
        return api_result

    def verify(self, intent: bytes) -> bytes:
        """
        I call POST /transactions/verify with the provided intent.

        :param intent: a jammed noun in binary representation of the intent.
        :return: an object that contains the result of the operation.
                 `{'valid?': boolean}`
        """
        encoded_intent = base64.b64encode(intent).decode("utf-8")
        payload = {"transaction": encoded_intent}
        api_result = self.__do_post("/transactions/verify", payload)
        return api_result
