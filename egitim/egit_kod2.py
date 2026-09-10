#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lennebraha-Coder egitimi: Qwen2.5-Coder-14B tabani, IKI LoRA + merge.
Modlar (MODE ortam degiskeni):
  turkce     -> lora_turkce egit (veri_seti3.json; sohbet/ustup veriniz)
  kod        -> lora_kod egit      (kod_verisi.json;  kod ornekleri)
  birlestir  -> iki adapteri taban üzerine ust uste ekleyip birleştir -> GGUF Q4_K_M -> HF
Ozet akis:
  python3 egit_kod.py MODE=turkce            # ~ dakikalar
  python3 egit_kod.py MODE=kod               # ~ saat
  MODE=birlestir python3 egit_kod.py         # GGUF + (istege bagli HF yukleme)
"""
import json, os, sys

MODE = os.environ.get("MODE", "kod")
TABAN = "Qwen/Qwen2.5-Coder-14B-Instruct"
MSEK = 4096
STEPLER = {"turkce": 150, "kod": 320}

def yukle_model():
    from unsloth import FastLanguageModel, is_bfloat16_supported
    model, tokenizer = FastLanguageModel.from_pretrained(
        TABAN, max_seq_length=MSEK, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=16, lora_alpha=16, lora_dropout=0, bias="none",
        use_gradient_checkpointing="unsloth",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"])
    return model, tokenizer, is_bfloat16_supported()

def egit(mode):
    from datasets import Dataset
    from transformers import TrainingArguments, logging as hflog
    from trl import SFTTrainer
    hflog.set_verbosity_info()
    yol = "veri_seti3.json" if mode == "turkce" else "kod_verisi.json"
    veri = json.load(open(yol, encoding="utf-8"))
    if not isinstance(veri, list):
        veri = veri.get("ornekler", veri)
    print("VERI: %s  (%d ornek)" % (yol, len(veri)))
    model, tokenizer, bf16 = yukle_model()
    rows = []
    for x in veri[:4000]:
        msgs = x.get("messages") or [{"role": "user", "content": x.get("soru", "")},
                                     {"role": "assistant", "content": x.get("kod", x.get("cevap", ""))}]
        if len(msgs) >= 2:
            rows.append({"text": tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)})
    ds = Dataset.from_list(rows)
    adim = STEPLER.get(mode, 300)
    arg = TrainingArguments(
        per_device_train_batch_size=2, gradient_accumulation_steps=1,
        warmup_steps=10, max_steps=adim,
        learning_rate=2e-4, fp16=not bf16, bf16=bf16,
        logging_steps=1, optim="adamw_8bit", weight_decay=0.01,
        lr_scheduler_type="linear", seed=42,
        output_dir="kayit_%s" % mode, report_to="none",
    )
    tr = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=ds,
                    dataset_text_field="text", max_seq_length=MSEK,
                    args=arg)
    tr.train()
    model.save_pretrained("lora_%s" % mode)
    tokenizer.save_pretrained("lora_%s" % mode)
    print("ADAPTER KAYDEDILDI: lora_%s" % mode)

def birlestir():
    from unsloth import FastLanguageModel
    print("Taban yukleniyor ...")
    model, tokenizer = yukle_model()
    print("Adapter eklenip dogrudan GGUF uretiliyor (lora_turkce + lora_kod) ...")
    model.save_pretrained_gguf("gguf_lenkod", quantization_method="q4_k_m",
                               adapter_names=["lora_turkce", "lora_kod"])
    import glob
    gguf = sorted(glob.glob("gguf_lenkod/*.gguf"))
    print("GGUF DOSYASI:", gguf)
    if not gguf:
        print("HATA: gguf bulunamadi - diski kontrol et (Kaggle /tmp'de yer vardir).")
        return
    if input("Hugging Face'e yukle? (e/h): ").strip().lower() == "e":
        from huggingface_hub import HfApi, login
        token = getpass("HF_TOKEN: ")
        login(token=token, add_to_git_credential=False)
        repo = "Lennebraha38/lennebraha-coder"
        api = HfApi()
        api.create_repo(repo, token=token, exist_ok=True)
        gguf = gguf[0]
        api.upload_file(path_or_fileobj=gguf, path_in_repo=os.path.basename(gguf),
                        repo_id=repo, token=token)
        modelfile = "FROM %s\nSYSTEM \"\"\"Sen Lennebraha38 tarafindan egitilmis kod asistanisin. Turkce sorulari anlar, calisan Python kodu yazar.\"\"\"" % os.path.basename(gguf)
        api.upload_file(path_or_fileobj=modelfile.encode(), path_in_repo="Modelfile", repo_id=repo, token=token)
        print("HF TAMAM: https://huggingface.co/%s" % repo)

if __name__ == "__main__":
    if MODE == "birlestir":
        birlestir()
    elif MODE in STEPLER:
        egit(MODE)
    else:
        print("MODE = turkce | kod | birlestir")