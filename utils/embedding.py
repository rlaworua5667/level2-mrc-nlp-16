import torch
from torch.utils.data import DataLoader
from tqdm import tqdm


def collate_fn(batch):
    input_ids = torch.cat([item["input_ids"] for item in batch])
    attention_mask = torch.cat([item["attention_mask"] for item in batch])
    overflow = torch.cat([item["overflow"] + idx for idx, item in enumerate(batch)])
    document = [item["document_id"] for item in batch]  ## context의 모든 chunk를 저장하기 위해 chunk 개수만큼 doc_id 반복

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "overflow": overflow,
        "document_id": document,
    }


def context_embedding(contextdataset, retrieval, batch_size=2):
    contextloader = DataLoader(contextdataset, batch_size)

    mod = retrieval.mod_c.to("cuda")
    mod.eval()

    embeddings = []
    doc_id = []
    for batch in tqdm(contextloader):
        with torch.no_grad():
            c_emb = mod(
                input_ids=batch["input_ids"].squeeze(1).to("cuda"),
                attention_mask=batch["attention_mask"].squeeze(1).to("cuda"),
            ).last_hidden_state[:, 0, :]

        embeddings.append(c_emb.to("cpu"))
        doc_id.extend(batch["document_id"])

        del c_emb

    return {
        "contexts_embedding": torch.cat(embeddings, dim=0),
        "document_id": doc_id,
    }
