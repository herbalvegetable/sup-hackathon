import logging
from app.schemas.benchmark import BenchmarkChunk, BenchmarkValues

logger = logging.getLogger(__name__)

SOURCE_ORDER = [
    "user_curated_document",
    "mas_financial_planning",
    "lia_protection_gap_study",
    "medishield_life_benefits",
    "moh_integrated_shield_plans",
]

# Categories to query from MOH IP comparison specifically
HOSPITAL_SOURCES = {"moh_integrated_shield_plans", "medishield_life_benefits"}


def get_chroma_collection():
    """Get or create the ChromaDB collection."""
    try:
        import chromadb
        from app.config import settings
        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        return client.get_or_create_collection(
            name="benchmark_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        logger.error(f"ChromaDB connection failed: {e}")
        return None


def query_source(
    collection,
    source_document: str,
    category: str,
    query_embedding: list[float],
    n_results: int = 1,
) -> list[BenchmarkChunk]:
    """Query a single source document for a specific coverage category."""
    if collection is None:
        return []

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                "$and": [
                    {"source_document": {"$eq": source_document}},
                    {"category": {"$eq": category}},
                ]
            },
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            score = 1.0 - distance  # convert cosine distance to similarity

            chunks.append(BenchmarkChunk(
                chunk_id=doc_id,
                text=results["documents"][0][i],
                source_document=source_document,
                source_page=meta.get("source_page"),
                category=category,
                score=score,
                value=meta.get("value"),
                value_high=meta.get("value_high"),
                value_type=meta.get("value_type"),
            ))
        return chunks
    except Exception as e:
        logger.warning(f"Query failed for {source_document}/{category}: {e}")
        return []


def get_embedding(text: str) -> list[float]:
    """Get embedding for a query string using OpenAI."""
    from openai import OpenAI
    from app.config import settings

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


COVERAGE_CATEGORIES = [
    "life", "ci", "early_ci", "tpd", "hospital", "disability",
    "careshield", "personal_accident"
]

CATEGORY_QUERY_TEXTS = {
    "life": "life insurance death benefit sum assured income multiplier",
    "ci": "critical illness coverage recommended amount multiplier",
    "early_ci": "early critical illness coverage",
    "tpd": "total permanent disability coverage",
    "hospital": "hospitalisation integrated shield plan ward tier",
    "disability": "disability income replacement percentage",
    "careshield": "careshield life supplement severe disability",
    "personal_accident": "personal accident insurance coverage",
}


def retrieve_benchmark_chunks(has_user_doc: bool = False) -> list[BenchmarkChunk]:
    """
    Query benchmark sources sequentially per category.
    Returns all retrieved chunks with metadata.
    """
    collection = get_chroma_collection()
    if collection is None:
        return []

    all_chunks: list[BenchmarkChunk] = []
    sources = SOURCE_ORDER if has_user_doc else SOURCE_ORDER[1:]

    for category in COVERAGE_CATEGORIES:
        query_text = CATEGORY_QUERY_TEXTS.get(category, category)
        try:
            query_embedding = get_embedding(query_text)
        except Exception as e:
            logger.warning(f"Could not get embedding for {category}: {e}")
            continue

        best_chunk: BenchmarkChunk | None = None

        for source in sources:
            # MOH IP comparison is only for hospital
            if source == "moh_integrated_shield_plans" and category != "hospital":
                continue

            chunks = query_source(collection, source, category, query_embedding)
            if chunks:
                chunk = chunks[0]
                # User-curated document overrides all others
                if source == "user_curated_document":
                    best_chunk = chunk
                    break
                # Keep highest-scoring chunk
                if best_chunk is None or chunk.score > best_chunk.score:
                    best_chunk = chunk

        if best_chunk:
            all_chunks.append(best_chunk)

    return all_chunks


def build_benchmark_values(chunks: list[BenchmarkChunk]) -> BenchmarkValues:
    """
    Convert retrieved chunks to structured BenchmarkValues.
    Reads value/value_high/value_type directly from chunk metadata.
    No LLM involved — fully deterministic.
    """
    bv = BenchmarkValues()

    for chunk in chunks:
        cat = chunk.category
        val = chunk.value
        val_high = chunk.value_high

        if cat == "life" and val is not None:
            bv.life_coverage_multiplier = val
            bv.life_coverage_multiplier_high = val_high
            bv.source_chunk_ids["life"] = chunk.chunk_id
            bv.source_chunk_texts["life"] = chunk.text

        elif cat == "ci" and val is not None:
            bv.ci_coverage_multiplier_low = val
            bv.ci_coverage_multiplier_high = val_high
            bv.source_chunk_ids["ci"] = chunk.chunk_id
            bv.source_chunk_texts["ci"] = chunk.text

        elif cat == "early_ci" and val is not None:
            bv.early_ci_coverage_multiplier = val
            bv.source_chunk_ids["early_ci"] = chunk.chunk_id
            bv.source_chunk_texts["early_ci"] = chunk.text

        elif cat == "tpd" and val is not None:
            bv.tpd_coverage_multiplier = val
            bv.source_chunk_ids["tpd"] = chunk.chunk_id
            bv.source_chunk_texts["tpd"] = chunk.text

        elif cat == "hospital" and chunk.value_type == "plan_tier":
            bv.hospital_recommended_ip_tier = chunk.text.strip()
            bv.source_chunk_ids["hospital"] = chunk.chunk_id
            bv.source_chunk_texts["hospital"] = chunk.text

        elif cat == "disability" and val is not None:
            bv.disability_income_replacement_pct = val
            bv.source_chunk_ids["disability"] = chunk.chunk_id
            bv.source_chunk_texts["disability"] = chunk.text

        elif cat == "careshield":
            bv.careshield_supplement_recommended = True
            bv.source_chunk_ids["careshield"] = chunk.chunk_id
            bv.source_chunk_texts["careshield"] = chunk.text

        elif cat == "personal_accident" and val is not None:
            bv.personal_accident_multiplier = val
            bv.source_chunk_ids["personal_accident"] = chunk.chunk_id
            bv.source_chunk_texts["personal_accident"] = chunk.text

    return bv


def get_fallback_benchmark_values() -> BenchmarkValues:
    """
    Return hardcoded fallback benchmark values based on MAS/LIA guidelines.
    Used when ChromaDB is unavailable.
    """
    return BenchmarkValues(
        life_coverage_multiplier=9.0,
        life_coverage_multiplier_high=10.0,
        ci_coverage_multiplier_low=3.9,
        ci_coverage_multiplier_high=5.0,
        early_ci_coverage_multiplier=2.0,
        tpd_coverage_multiplier=9.0,
        disability_income_replacement_pct=0.75,
        hospital_recommended_ip_tier="B1",
        careshield_supplement_recommended=True,
        personal_accident_multiplier=1.0,
        source_chunk_ids={},
        source_chunk_texts={
            "life": "MAS recommends life coverage of 9–10x annual income for working adults with dependents.",
            "ci": "LIA Protection Gap Study 2022 recommends critical illness coverage of 3.9–5x annual income.",
            "early_ci": "Early critical illness coverage is recommended at approximately 2x annual income.",
            "tpd": "TPD coverage is typically benchmarked alongside life coverage at 9–10x annual income.",
            "disability": "MAS recommends disability income coverage replacing 75% of monthly income.",
            "hospital": "MOH recommends at least a Class B1 Integrated Shield Plan for adequate hospitalisation coverage.",
            "careshield": "CareShield Life enrollees should consider a supplement to cover daily expenses during severe disability.",
            "personal_accident": "Personal accident coverage is typically 1–2x annual income.",
        },
    )
