class LLMConfig:
    """
    Configuration class for LLM generation parameters.

    :param temperature: Controls randomness in the output (0.0 to 2.0)
    :param top_p: Controls diversity via nucleus sampling (0.0 to 1.0)
    :param top_k: Controls diversity by limiting to K most likely tokens
    :param max_token: Controls the max number of output tokens
    """

    def __init__(
            self,
            temperature: float,
            top_p: float,
            top_k: int,
            max_token: int
    ) -> None:
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if not (0.0 <= top_p <= 1.0):
            raise ValueError("Top-p must be between 0.0 and 1.0")

        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
        self._max_token = max_token

    @property
    def temperature(self) -> float:
        """
        Gets the temperature parameter.
        :return: The temperature value (0.0 to 2.0)
        """
        return self._temperature

    @property
    def top_p(self) -> float:
        """
        Gets the top-p parameter.
        :return: The top-p value (0.0 to 1.0)
        """
        return self._top_p

    @property
    def top_k(self) -> int:
        """
        Gets the top-k parameter.
        :return: The top-k value
        """
        return self._top_k

    @property
    def max_token(self) -> int:
        """
        Gets the max output token parameter.
        :return: The number of tokens
        """
        return self._max_token