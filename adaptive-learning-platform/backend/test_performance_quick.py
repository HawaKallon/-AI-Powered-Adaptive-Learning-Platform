#!/usr/bin/env python3
"""Quick performance test to find bottlenecks"""

import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

print("Starting performance diagnostic...\n")

# Test 1: Database connection
print("1. Testing database connection...")
start = time.time()
try:
    from app.database import get_db
    db = next(get_db())
    print(f"   ✓ Database connected in {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ✗ Database error: {e}")

# Test 2: Embedding service initialization
print("\n2. Testing embedding service...")
start = time.time()
try:
    from app.utils.embeddings import get_embedding_service
    embedding_service = get_embedding_service()
    print(f"   ✓ Embedding service ready in {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ✗ Embedding service error: {e}")

# Test 3: Curriculum search
print("\n3. Testing curriculum search...")
start = time.time()
try:
    from app.services.curriculum_ingestion import get_curriculum_ingestion_service
    service = get_curriculum_ingestion_service()
    results = service.search_curriculum_content("algebra", subject="mathematics", grade=10, n_results=3)
    print(f"   ✓ Search completed in {time.time() - start:.2f}s ({len(results)} results)")
except Exception as e:
    print(f"   ✗ Search error: {e}")

# Test 4: Content generator initialization
print("\n4. Testing content generator...")
start = time.time()
try:
    from app.services.content_generator import get_content_generator_service
    generator = get_content_generator_service()
    print(f"   ✓ Content generator ready in {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ✗ Content generator error: {e}")

# Test 5: Lesson generation
print("\n5. Testing lesson generation...")
start = time.time()
try:
    from app.models import Student
    student = db.query(Student).first()
    if student:
        result = generator.generate_personalized_lesson(
            student_id=str(student.id),
            subject="mathematics",
            topic="algebra",
            db=db
        )
        elapsed = time.time() - start
        if result['success']:
            print(f"   ✓ Lesson generated in {elapsed:.2f}s")
        else:
            print(f"   ✗ Generation failed: {result.get('error')}")
    else:
        print(f"   ⚠ No student found for testing")
except Exception as e:
    print(f"   ✗ Lesson generation error: {e}")

print("\n" + "="*60)
print("DIAGNOSIS:")
if elapsed > 10:
    print("⚠️  SLOW: Lesson generation taking > 10 seconds")
    print("   Issue: ChromaDB or database queries are slow")
elif elapsed > 5:
    print("⚠️  MODERATE: Generation taking 5-10 seconds")
    print("   May cause timeouts on slower connections")
else:
    print("✓ FAST: Generation under 5 seconds - should work fine")
print("="*60)

