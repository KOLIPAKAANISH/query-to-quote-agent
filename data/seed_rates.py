"""
Seed ChromaDB with sample supplier rate sheet snippets.
Run this once to populate the vector store, or it auto-seeds on import.
"""

import chromadb

# Sample supplier rate data — 12 snippets across Bali, Goa, Maldives, Thailand
RATE_SNIPPETS = [
    # --- Bali ---
    {
        "id": "bali-resort-ubud",
        "text": "Bali Resort Package — Ubud Aura Retreat: 5N/6D, includes airport transfer, breakfast, 1 spa session. ₹42,000/pax twin-share, Dec-Feb season.",
        "destination": "Bali",
        "category": "resort",
    },
    {
        "id": "bali-flights-blr",
        "text": "Bali Flights — BLR/HYD to DPS via Singapore, round trip economy, ₹28,000-34,000/pax depending on booking window.",
        "destination": "Bali",
        "category": "flights",
    },
    {
        "id": "bali-resort-seminyak",
        "text": "Bali Beach Resort — Seminyak Sands: 4N/5D beachfront, breakfast & dinner included, pool access. ₹38,000/pax twin-share.",
        "destination": "Bali",
        "category": "resort",
    },
    {
        "id": "bali-activities",
        "text": "Bali Activities Package — Rice terrace trek, temple visits, waterfall tour, snorkeling. Full day ₹6,500/pax.",
        "destination": "Bali",
        "category": "activities",
    },
    # --- Goa ---
    {
        "id": "goa-villa-private",
        "text": "Goa Villa Package — 4N/5D private pool villa, 4 pax, ₹65,000 total, includes breakfast.",
        "destination": "Goa",
        "category": "resort",
    },
    {
        "id": "goa-beach-resort",
        "text": "Goa Beach Resort — Calangute Breeze: 3N/4D, sea-view room, breakfast included, near Baga Beach. ₹18,000/pax.",
        "destination": "Goa",
        "category": "resort",
    },
    {
        "id": "goa-activities",
        "text": "Goa Activities — Water sports bundle (parasailing, jet ski, banana ride) + Old Goa heritage tour. ₹4,500/pax full day.",
        "destination": "Goa",
        "category": "activities",
    },
    # --- Maldives ---
    {
        "id": "maldives-resort-overwater",
        "text": "Maldives Overwater Villa — Sun Siyam Vilu Reef: 4N/5D, all-inclusive, water villa with glass floor. ₹1,80,000/pax twin-share.",
        "destination": "Maldives",
        "category": "resort",
    },
    {
        "id": "maldives-flights",
        "text": "Maldives Flights — BLR/DEL to MLE, direct + connecting options, ₹22,000-40,000/pax round trip.",
        "destination": "Maldives",
        "category": "flights",
    },
    # --- Thailand ---
    {
        "id": "thailand-resort-phuket",
        "text": "Thailand Resort — Phuket Palm Paradise: 5N/6D, beachfront, breakfast & lunch, airport transfer. ₹35,000/pax twin-share.",
        "destination": "Thailand",
        "category": "resort",
    },
    {
        "id": "thailand-flights",
        "text": "Thailand Flights — BLR/HYD to BKK, round trip economy, ₹18,000-25,000/pax depending on season.",
        "destination": "Thailand",
        "category": "flights",
    },
    {
        "id": "thailand-activities",
        "text": "Thailand Activities — Phi Phi island day trip, elephant sanctuary visit, Thai cooking class. ₹8,000/pax full day.",
        "destination": "Thailand",
        "category": "activities",
    },
]


def get_collection(client=None):
    """Get or create the ChromaDB collection, seeding if empty."""
    if client is None:
        client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(
        name="supplier_rates",
        metadata={"hnsw:space": "cosine"},
    )

    # Seed if empty
    if collection.count() == 0:
        documents = [s["text"] for s in RATE_SNIPPETS]
        ids = [s["id"] for s in RATE_SNIPPETS]
        metadatas = [{"destination": s["destination"], "category": s["category"]} for s in RATE_SNIPPETS]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"Seeded {len(RATE_SNIPPETS)} rate snippets into ChromaDB")

    return collection


def search_rates(query: str, n_results: int = 3, client=None):
    """Search for relevant rate snippets."""
    collection = get_collection(client)
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0] if results["documents"] else []


if __name__ == "__main__":
    # Quick test
    rates = search_rates("Bali resort activities")
    print(f"\nFound {len(rates)} results for 'Bali resort activities':")
    for i, r in enumerate(rates, 1):
        print(f"  {i}. {r[:80]}...")
