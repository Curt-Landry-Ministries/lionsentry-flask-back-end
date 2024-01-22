import re

# TODO implement these to track the cost of each function, and update with gpt4-1106-preview costs

def token_counter(text):
    tokens = re.findall(r'\b\w+\b|[^a-zA-Z0-9\s]', text)
    return len(tokens)

def calculate_api_cost(input_tokens, output_tokens):
    input_cost = 0.03 * (input_tokens / 1000)
    output_cost = 0.06 * (output_tokens / 1000)
    return round(input_cost + output_cost, 4)