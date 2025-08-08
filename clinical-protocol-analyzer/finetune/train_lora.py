import argparse, yaml, os
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model

def format_example(ex):
    return ex["prompt"] + "\n\n### Answer\n" + ex["completion"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))

    model_name = cfg["model_name"]
    dataset_path = cfg["dataset_path"]
    out_dir = cfg["output_dir"]
    os.makedirs(out_dir, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # LoRA
    lc = cfg["lora"]
    lora_cfg = LoraConfig(
        r=lc["r"],
        lora_alpha=lc["alpha"],
        lora_dropout=lc["dropout"],
        target_modules=lc["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    ds = load_dataset("json", data_files=dataset_path, split="train")

    def preprocess(example):
        text = format_example(example)
        enc = tokenizer(text, truncation=True, padding="max_length", max_length=cfg["train"]["max_seq_len"])
        enc["labels"] = enc["input_ids"].copy()
        return enc

    ds = ds.map(preprocess, batched=False)
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=cfg["train"]["batch_size"],
        gradient_accumulation_steps=cfg["train"]["grad_accum_steps"],
        learning_rate=cfg["train"]["lr"],
        num_train_epochs=cfg["train"]["epochs"],
        fp16=False,
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=ds,
        data_collator=collator,
    )
    trainer.train()
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    print("Training complete. LoRA adapters saved to", out_dir)

if __name__ == "__main__":
    main()
