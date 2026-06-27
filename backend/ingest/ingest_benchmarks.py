"""
Ingestion script for benchmark knowledge base.
Run this once to populate ChromaDB with benchmark data.
Usage: python -m ingest.ingest_benchmarks
"""
import os
import sys
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


# Structured benchmark chunks with metadata
# Each chunk stores both text and structured metadata for deterministic retrieval
BENCHMARK_CHUNKS = [
    # MAS Financial Planning Guide
    {
        "id": "mas_life_001",
        "text": "MAS recommends life insurance coverage of 9 to 10 times annual income for working adults with dependents. This accounts for income replacement, outstanding debts, and dependents' future expenses.",
        "metadata": {
            "category": "life",
            "source_document": "mas_financial_planning",
            "source_page": "12",
            "value": 9.0,
            "value_high": 10.0,
            "value_type": "income_multiplier",
        },
    },
    {
        "id": "mas_tpd_001",
        "text": "Total Permanent Disability (TPD) coverage should be equivalent to life coverage — approximately 9 to 10 times annual income — as it replaces earning capacity permanently lost due to disability.",
        "metadata": {
            "category": "tpd",
            "source_document": "mas_financial_planning",
            "source_page": "13",
            "value": 9.0,
            "value_high": 10.0,
            "value_type": "income_multiplier",
        },
    },
    {
        "id": "mas_disability_001",
        "text": "MAS recommends disability income insurance replacing 75% of monthly income to cover living expenses if unable to work due to illness or injury.",
        "metadata": {
            "category": "disability",
            "source_document": "mas_financial_planning",
            "source_page": "14",
            "value": 0.75,
            "value_high": None,
            "value_type": "percentage",
        },
    },
    # LIA Protection Gap Study 2022
    {
        "id": "lia_ci_001",
        "text": "The LIA Protection Gap Study 2022 recommends critical illness coverage of 3.9 to 5 times annual income. Singapore has a significant CI protection gap — 7 in 10 Singaporeans are underinsured for critical illness.",
        "metadata": {
            "category": "ci",
            "source_document": "lia_protection_gap_study",
            "source_page": "24",
            "value": 3.9,
            "value_high": 5.0,
            "value_type": "income_multiplier",
        },
    },
    {
        "id": "lia_early_ci_001",
        "text": "Early critical illness (early CI) coverage pays out at early detection before conditions progress to late stage. LIA recommends approximately 2 times annual income for early CI coverage.",
        "metadata": {
            "category": "early_ci",
            "source_document": "lia_protection_gap_study",
            "source_page": "26",
            "value": 2.0,
            "value_high": 2.5,
            "value_type": "income_multiplier",
        },
    },
    {
        "id": "lia_pa_001",
        "text": "Personal accident insurance is recommended at 1 to 2 times annual income. Higher coverage is warranted for those in high-risk occupations such as construction or delivery.",
        "metadata": {
            "category": "personal_accident",
            "source_document": "lia_protection_gap_study",
            "source_page": "30",
            "value": 1.0,
            "value_high": 2.0,
            "value_type": "income_multiplier",
        },
    },
    # MediShield Life Benefits
    {
        "id": "medishield_careshield_001",
        "text": "CareShield Life provides long-term care insurance for severe disability. All Singapore Citizens and PRs born in 1980 or later are automatically enrolled. Those enrolled should consider a supplement policy to top up the monthly payout to cover actual disability care costs.",
        "metadata": {
            "category": "careshield",
            "source_document": "medishield_life_benefits",
            "source_page": "careshield-section",
            "value": 1.0,
            "value_high": None,
            "value_type": "boolean",
        },
    },
    # MOH Integrated Shield Plans
    {
        "id": "moh_hospital_b1_001",
        "text": "Class B1 is the recommended minimum tier for Integrated Shield Plans. It provides adequate coverage at a reasonable premium while allowing use of Class B1 wards at restructured hospitals. All Singapore Citizens and PRs should have at minimum a Class B1 IP rider.",
        "metadata": {
            "category": "hospital",
            "source_document": "moh_integrated_shield_plans",
            "source_page": "comparison-table",
            "value": None,
            "value_high": None,
            "value_type": "plan_tier",
        },
    },
]


def ingest():
    import chromadb
    from openai import OpenAI

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    collection = client.get_or_create_collection(
        name="benchmark_knowledge",
        metadata={"hnsw:space": "cosine"},
    )

    print("Connecting to OpenAI for embeddings...")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    print(f"Ingesting {len(BENCHMARK_CHUNKS)} chunks...")

    for chunk in BENCHMARK_CHUNKS:
        print(f"  Embedding: {chunk['id']}")
        response = openai_client.embeddings.create(
            model=settings.embedding_model,
            input=chunk["text"],
        )
        embedding = response.data[0].embedding

        # Store metadata, converting None to empty string for ChromaDB compatibility
        metadata = {}
        for k, v in chunk["metadata"].items():
            if v is None:
                metadata[k] = ""
            elif isinstance(v, float):
                metadata[k] = v
            else:
                metadata[k] = str(v)

        collection.upsert(
            ids=[chunk["id"]],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[metadata],
        )

    print(f"\n✓ Ingested {len(BENCHMARK_CHUNKS)} chunks into ChromaDB at {settings.chroma_db_path}")
    print("  Sources ingested:")
    sources = set(c["metadata"]["source_document"] for c in BENCHMARK_CHUNKS)
    for s in sorted(sources):
        count = sum(1 for c in BENCHMARK_CHUNKS if c["metadata"]["source_document"] == s)
        print(f"    - {s}: {count} chunks")


if __name__ == "__main__":
    ingest()
