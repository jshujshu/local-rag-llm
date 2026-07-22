# quantize.py

import os
import argparse
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

def main():
    parser = argparse.ArgumentParser(description="Download and quantize a Hugging Face model to 4-bit, then save it locally.")
    parser.add_argument(
        "--model", 
        type=str, 
        default="HauhauCS/Qwen3.5-4B-Uncensored-HauhauCS-Aggressive", 
        help="Hugging Face model repository ID."
    )
    parser.add_argument(
        "--name", 
        type=str, 
        default="qwen3.5-4b-uncensored-4bit", 
        help="Local directory name in snapshots/ where the quantized model will be saved."
    )
    args = parser.parse_args()

    # Enforce online mode temporarily to download model from the Hub
    os.environ["HF_HUB_OFFLINE"] = "0"
    if "HF_HUB_OFFLINE" in os.environ:
        print("Note: HF_HUB_OFFLINE environment variable detected, forcing to '0' for download.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "snapshots", args.name)
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================")
    print(f"Starting quantization for model: {args.model}")
    print(f"Saving quantized output to: {output_dir}")
    print("==================================================")

    print("Step 1: Downloading & loading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model)
        tokenizer.save_pretrained(output_dir)
        print("Tokenizer saved successfully.")
    except Exception as e:
        print(f"Error loading/saving tokenizer: {e}", file=sys.stderr)
        sys.exit(1)

    print("Step 2: Downloading, quantizing to 4-bit on-the-fly, and loading model...")
    print("This might take a while depending on model size and your network connection.")
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    try:
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            quantization_config=bnb_config,
            device_map={"": 0}
        )
        print(f"Model loaded and quantized on GPU: {model.device}")
    except Exception as e:
        print(f"Error loading and quantizing model: {e}", file=sys.stderr)
        sys.exit(1)

    print("Step 3: Saving quantized model weights and configurations to disk...")
    try:
        model.save_pretrained(output_dir)
        print("Model saved successfully.")
    except Exception as e:
        print(f"Error saving model: {e}", file=sys.stderr)
        sys.exit(1)

    print("==================================================")
    print("Quantization complete!")
    print(f"Model keys and weights are saved in: {output_dir}")
    print("You can now load this model in 100% offline mode.")
    print("==================================================")

if __name__ == "__main__":
    main()
