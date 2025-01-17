from openai import OpenAI

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

history = [
    {"role": "system", "content": "As Jarvis an AI voice assistant, you will be provided with various data in JSON format. Your job is to interpret the data and respond with a short, precise sentence suitable for voice output. The response should be natural and easy to understand.Always respond with sentences respond in french."}
]


def appel_llm(history):
        completion = client.chat.completions.create(
            model="lmstudio-community/Llama-3.2-1B-Instruct-GGUF",
            messages=history,
            temperature=0.7,
            stream=True,
        )

        new_message = {"role": "assistant", "content": ""}
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                new_message["content"] += chunk.choices[0].delta.content


def main():
    global history  # pour accéder à la variable globale
    while True:
        print()
        user_input = input("> ")
        history = [{"role": "user", "content": user_input}]  # nouveau message ajouté
        appel_llm(history)


if __name__ == "__main__":
    main()