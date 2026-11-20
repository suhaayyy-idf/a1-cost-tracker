import json
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI


def get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"Error: {name} must be a valid number, got '{raw}'.")
        sys.exit(1)


def call_openrouter(prompt: str, model: str, api_key: str) -> tuple[str, int, int, float]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    start = time.perf_counter()
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.perf_counter() - start

    choice = completion.choices[0] if completion.choices else None
    reply = (choice.message.content or "") if (choice and choice.message) else ""
    usage = getattr(completion, "usage", None)
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    return reply, input_tokens, output_tokens, elapsed


def call_groq(prompt: str, model: str, api_key: str) -> tuple[str, int, int, float]:
    client = Groq(api_key=api_key)
    start = time.perf_counter()
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.perf_counter() - start

    choice = completion.choices[0] if completion.choices else None
    reply = (choice.message.content or "") if (choice and choice.message) else ""
    usage = getattr(completion, "usage", None)
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    return reply, input_tokens, output_tokens, elapsed


def calculate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    input_price_per_m: float,
    output_price_per_m: float,
) -> float:
    return (input_tokens * input_price_per_m) / 1_000_000 + (
        output_tokens * output_price_per_m
    ) / 1_000_000


def print_summary_table(rows: list[dict[str, Any]]) -> None:
    headers = ["provider", "input tokens", "output tokens", "seconds", "cost in USD"]
    formatted_rows = [
        [
            r["provider"],
            str(r["input_tokens"]),
            str(r["output_tokens"]),
            f"{r['seconds']:.2f}",
            f"${r['cost_usd']:.8f}",
        ]
        for r in rows
    ]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in formatted_rows))
        for i in range(len(headers))
    ]

    def fmt_line(vals: list[str]) -> str:
        return " | ".join(vals[i].ljust(widths[i]) for i in range(len(headers)))

    sep = "-+-".join("-" * w for w in widths)
    print("\n=== Summary Table ===")
    print(fmt_line(headers))
    print(sep)
    for row in formatted_rows:
        print(fmt_line(row))


def main() -> None:
    load_dotenv()

    if len(sys.argv) < 2 or not " ".join(sys.argv[1:]).strip():
        print('Usage: uv run tracker.py "your prompt"')
        sys.exit(1)

    prompt = " ".join(sys.argv[1:]).strip()

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    missing = []
    if not openrouter_key:
        missing.append("OPENROUTER_API_KEY")
    if not groq_key:
        missing.append("GROQ_API_KEY")

    if missing:
        print(
            "Error: Missing required API key(s) in .env/environment: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and add your keys."
        )
        sys.exit(1)

    or_model = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    or_in_price = get_float_env("OPENROUTER_INPUT_PRICE_PER_M", 0.0)
    or_out_price = get_float_env("OPENROUTER_OUTPUT_PRICE_PER_M", 0.0)
    groq_in_price = get_float_env("GROQ_INPUT_PRICE_PER_M", 0.59)
    groq_out_price = get_float_env("GROQ_OUTPUT_PRICE_PER_M", 0.79)

    providers = [
        ("openrouter", or_model, call_openrouter, openrouter_key, or_in_price, or_out_price),
        ("groq", groq_model, call_groq, groq_key, groq_in_price, groq_out_price),
    ]

    results_for_json: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []

    for name, model_name, fn, key, in_price, out_price in providers:
        try:
            reply, in_tok, out_tok, elapsed = fn(prompt, model_name, key)
        except Exception as exc:
            print(f"Error calling {name} ({model_name}): {exc}")
            sys.exit(1)

        cost_usd = calculate_cost_usd(in_tok, out_tok, in_price, out_price)

        print(f"\n--- {name.upper()} ({model_name}) ---")
        print(reply)

        results_for_json.append(
            {
                "provider": name,
                "model": model_name,
                "reply": reply,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "input_price_per_m": in_price,
                "output_price_per_m": out_price,
                "cost_usd": cost_usd,
            }
        )
        table_rows.append(
            {
                "provider": name,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "seconds": elapsed,
                "cost_usd": cost_usd,
            }
        )

    print_summary_table(table_rows)

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results_for_json, f, indent=2, ensure_ascii=False)

    print("\nSaved results.json")


if __name__ == "__main__":
    main()