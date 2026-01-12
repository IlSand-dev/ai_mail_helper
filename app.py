from collections import defaultdict
import os
import json
import torch
from typing import List, Optional, Dict
from fastapi import FastAPI
from pydantic import BaseModel, Field
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI(title="Mail AI Agent (read-only)")

MODEL_ID = os.getenv(
    "MODEL_ID",
    "mistralai/Mistral-7B-Instruct-v0.3")
ADAPTER_DIR = "./mistral-7b-ru-qlora/checkpoint-500"

tok = AutoTokenizer.from_pretrained(MODEL_ID)
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
)
model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.eval()


def generate_json(messages, max_new_tokens=256, temperature=0.1):
    prompt = tok.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tok.eos_token_id,
        )
    gen = out[0][inputs.input_ids.shape[1]:]
    text = tok.decode(gen, skip_special_tokens=True).strip()
    return json.loads(text)


class Email(BaseModel):
    id: Optional[str] = None
    thread_id: Optional[str] = None
    sender: Optional[str] = None
    subject: str
    body: str
    labels: Optional[List[str]] = None


class SummarizeEmailIn(BaseModel):
    email: Email
    short: bool = True


class SummarizeThreadIn(BaseModel):
    emails: List[Email]
    short: bool = True


class SummarizeOut(BaseModel):
    summary: List[str]


class SpamIn(BaseModel):
    email: Email


class SpamOut(BaseModel):
    label: str
    reasons: List[str]


class PrioritizeIn(BaseModel):
    email: Email


class PrioritizeOut(BaseModel):
    priority: str
    reasons: List[str]
    categories: List[str]


class DigestIn(BaseModel):
    emails: List[Email]
    period: str = Field("daily", pattern="^(daily|weekly)$")
    group_by: Optional[str] = Field(
        "labels", description="labels|sender|thread")


class DigestGroup(BaseModel):
    key: str
    items: List[Dict[str, str]]


class DigestOut(BaseModel):
    period: str
    groups: List[DigestGroup]
    highlights: List[str]


@app.post("/summarize/email", response_model=SummarizeOut)
def summarize_email(payload: SummarizeEmailIn):
    system_txt = 'Ты помощник по почте. Верни ТОЛЬКО JSON строго по схеме и без других ключей: {"summary": [str, ...]}. Без переносов строк внутри элементов и без пунктов вида "1.".'

    if payload.short:
        style = "кратко, 3-5 пунктов"
    else:
        style = "подробно, 6-10 пунктов и ключевые факты"

    user_txt = f"Тема: {payload.email.subject}\nТело:\n{payload.email.body}\nФормат: {style}."
    messages = [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]
    data = generate_json(messages, max_new_tokens=300, temperature=0.0)
    return SummarizeOut(summary=data.get("summary", data.get("")))


@app.post("/summarize/thread", response_model=SummarizeOut)
def summarize_thread(payload: SummarizeThreadIn):
    system_txt = 'Ты помощник по почте. Суммаризируй тред. Верни ТОЛЬКО JSON строго по схеме и без других ключей:{"summary": [str, ...]}. Без переносов строк внутри элементов и без пунктов вида "1.".'

    if payload.short:
        style = "кратко, 5-7 пунктов: цель, решения, next steps"
    else:
        style = "подробно, 8-12 пунктов: контекст, решения, "
        "споры, next steps и владельцы"

    parts = []
    for i, e in enumerate(payload.emails, 1):
        parts.append(f"[{i}] {e.sender or 'unknown'} | {e.subject}\n{e.body}")

    user_txt = "Тред:\n" + "\n\n".join(parts) + f"\n\nФормат: {style}."
    messages = [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]
    data = generate_json(messages, max_new_tokens=300, temperature=0.0)
    return SummarizeOut(summary=data.get("summary", []))


@app.post("/classify/spam", response_model=SpamOut)
def classify_spam(payload: SpamIn):
    system_txt = ('Ты классификатор почты. Верни ТОЛЬКО JSON: '
                  '{"label": "спам"|"не спам", "reasons": [str,...]}.')
    user_txt = f"Тема: {payload.email.subject}"
    f"\nТело:\n{payload.email.body}\nКритерии: классический спам-фильтр."
    messages = [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]
    data = generate_json(messages, max_new_tokens=200, temperature=0.0)
    return SpamOut(
        label=data.get("label", "не спам"), reasons=data.get("reasons", [])
    )


@app.post("/prioritize", response_model=PrioritizeOut)
def prioritize(payload: PrioritizeIn):
    system_txt = (
        'Ты помогаешь приоритизировать письма. Верни ТОЛЬКО JSON, '
        'Без переносов строк внутри элементов и без пунктов вида "1.": '
        '{"priority": "Высокий"|"Средний"|"Низкий", "reasons": [str], '
        '"categories": ["billing","hr","contracts","urgent","other"]}.')
    meta = f"Отправитель: {payload.email.sender or 'unknown'}; "
    f"Лейблы: {payload.email.labels or []}"

    user_txt = f"{meta}\nТема: {payload.email.subject}\n"
    f"Тело:\n{payload.email.body}\n"
    "Правила: важнее биллинг/HR/контракты/срочно."

    messages = [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]
    data = generate_json(messages, max_new_tokens=220, temperature=0.1)
    return PrioritizeOut(
        priority=data.get("priority", "medium"),
        reasons=data.get("reasons", []),
        categories=data.get("categories", ["other"])
    )


@app.post("/digest", response_model=DigestOut)
def digest(payload: DigestIn):
    # группировка по labels|sender|thread
    groups_map = defaultdict(list)
    if payload.group_by == "sender":
        for e in payload.emails:
            groups_map[e.sender or "unknown"].append(e)
    elif payload.group_by == "thread":
        for e in payload.emails:
            groups_map[e.thread_id or "no-thread"].append(e)
    else:
        for e in payload.emails:
            labs = e.labels or ["UNLABELED"]
            for lb in labs:
                groups_map[lb].append(e)

    out_groups, all_highlights = [], []
    for key, items in groups_map.items():
        summaries = []
        for e in items[:20]:
            system_txt = 'Суммаризируй письмо в 1-2 предложения. '
            'Верни ТОЛЬКО JSON: {"summary": str}.'
            user_txt = f"Тема: {e.subject}\nТело:\n{e.body}"

            msgs = [
                {"role": "system", "content": system_txt},
                {"role": "user", "content": user_txt}
            ]
            data = generate_json(msgs, max_new_tokens=120, temperature=0.2)
            summaries.append(
                {
                    "id": e.id or "",
                    "subject": e.subject,
                    "short_summary": data.get("summary", "")
                }
            )

        system2 = 'Сделай 3-5 highlights по группе писем. '
        'Верни ТОЛЬКО JSON: {"highlights": [str]}.'

        joined = "\n".join(
            [f"- {s['subject']}: {s['short_summary']}" for s in summaries])

        msgs2 = [{"role": "system", "content": system2}, {
            "role": "user", "content": f"Группа: {key}\nСводки:\n{joined}"}]
        d2 = generate_json(msgs2, max_new_tokens=150, temperature=0.2)
        all_highlights.extend(d2.get("highlights", []))
        out_groups.append(DigestGroup(key=key, items=summaries))

    return DigestOut(period=payload.period, groups=out_groups,
                     highlights=all_highlights[:20])
