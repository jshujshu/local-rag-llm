# llm.py

import os
import gc
import time
import threading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer, BitsAndBytesConfig
from config import MAX_NEW_TOKENS, LLM_IDLE_TIMEOUT, QUANTIZED_MODELS

_tokenizer = None
_model = None
_loaded_model_name = None
_generation_lock = threading.Lock()
_last_active_time = 0.0

def unload_model():
    global _model, _tokenizer, _loaded_model_name
    if _model is not None:
        print(f"Unloading model {_loaded_model_name}...")
        del _model
        del _tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    _model = None
    _tokenizer = None
    _loaded_model_name = None


def _log_model_device(model_name: str):
    """Print which device each parameter group landed on after loading."""
    devices = {str(p.device) for p in _model.parameters()}
    print(f"[llm] Model '{model_name}' loaded on device(s): {sorted(devices)}")
    if torch.cuda.is_available():
        used  = torch.cuda.memory_allocated(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"[llm] VRAM usage: {used:.2f} GB / {total:.2f} GB")


def load_model(model_name: str):
    global _tokenizer, _model, _loaded_model_name, _last_active_time
    if _loaded_model_name == model_name:
        _last_active_time = time.time()
        return
    unload_model()
    print(f"Loading model {model_name}...")
    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    # Determine if this model should be loaded in 4-bit
    should_quantize = False
    if model_name in QUANTIZED_MODELS:
        should_quantize = True
    else:
        base = os.path.basename(model_name.rstrip("/\\"))
        if base in QUANTIZED_MODELS:
            should_quantize = True

    load_kwargs = {}

    if should_quantize:
        print(f"Applying 4-bit quantization configuration for {model_name}...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        load_kwargs["quantization_config"] = bnb_config
        load_kwargs["device_map"] = {"": 0}
    else:
        # Fix: force all layers to GPU 0 instead of device_map='auto'.
        # 'auto' silently spills layers to CPU when VRAM is tight (e.g.
        # when the embedding model is already resident), causing the LLM
        # to run mostly on CPU with no warning. Using device_map={'': 0}
        # makes OOM fail loudly if VRAM is truly insufficient, and
        # ensures all layers are on CUDA when there is enough headroom.
        load_kwargs["device_map"] = {"": 0}
        load_kwargs["torch_dtype"] = torch.float16

    _model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **load_kwargs
    )
    _model.eval()
    _loaded_model_name = model_name
    _last_active_time = time.time()
    _log_model_device(model_name)


def generate_stream(messages: list, model_name: str, max_new_tokens: int = MAX_NEW_TOKENS):
    global _last_active_time
    with _generation_lock:
        load_model(model_name)
        _last_active_time = time.time()
        
        prompt_text = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = _tokenizer(prompt_text, return_tensors="pt").to(_model.device)
        streamer = TextIteratorStreamer(
            _tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        thread = threading.Thread(
            target=_model.generate,
            kwargs=dict(
                **inputs,
                streamer=streamer,
                max_new_tokens=max_new_tokens,
                temperature=0.2,
                do_sample=True,
                pad_token_id=_tokenizer.eos_token_id
            )
        )
        thread.start()
        for text in streamer:
            _last_active_time = time.time()
            yield text
        thread.join()
        _last_active_time = time.time()


def _idle_cleanup_worker():
    global _last_active_time
    while True:
        time.sleep(10)
        # Attempt to acquire lock without blocking indefinitely to check status
        acquired = _generation_lock.acquire(blocking=False)
        if acquired:
            try:
                if _loaded_model_name is not None:
                    if time.time() - _last_active_time > LLM_IDLE_TIMEOUT:
                        print(f"Model {_loaded_model_name} has been idle for >{LLM_IDLE_TIMEOUT}s. Auto-unloading.")
                        unload_model()
            finally:
                _generation_lock.release()

# Start background cleanup thread
cleanup_thread = threading.Thread(target=_idle_cleanup_worker, daemon=True)
cleanup_thread.start()

