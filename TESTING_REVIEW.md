# Testing Review Queue Triggering

## What is Textract Used For?

**AWS Textract** performs **OCR (Optical Character Recognition)**:

- Converts PDF/image files → **raw text**
- This text is then fed to the **LLM extractor** to extract structured fields
- Without Textract, you can't process scanned PDFs or images

### Workflow Flow:

```
PDF/Image Upload
    ↓
Textract (OCR) → Raw text string
    ↓
LLM Extractor → Structured fields (invoice_number, vendor_name, etc.)
    ↓
Confidence Computation → Per-field confidence scores
    ↓
Validation → Check errors + confidence thresholds
    ↓
Review Gate → Create ReviewItem if validation fails OR confidence too low
```

## How to Trigger a Review Item

A **ReviewItem** is created when **either**:

1. **Validation errors** exist (missing/invalid fields)
2. **Low confidence** scores (< threshold)

### Method 1: Validation Errors (Easiest)

Upload a document that will fail validation:

**Option A: Missing Required Fields**

- Upload a PDF/image that doesn't contain invoice_number, vendor_name, total_amount, currency, or invoice_date
- The LLM will return null/empty for these → validation fails → review triggered

**Option B: Invalid Currency**

- Upload an invoice with currency like "XYZ" or "NGN" (not in supported list: USD, EUR, GBP, CHF)
- Validation fails → review triggered

**Option C: Invalid Date Format**

- Upload an invoice where the date can't be parsed as ISO format (YYYY-MM-DD)
- Validation fails → review triggered

### Method 2: Low Confidence Scores

The confidence calculator uses heuristics. To trigger low confidence:

**Option A: Poor OCR Quality**

- Upload a scanned PDF/image with:
  - Blurry text
  - Low resolution
  - Handwritten text
  - Text that doesn't match expected patterns
- Textract may extract garbled text → LLM extracts fields → confidence heuristics detect poor quality → review triggered

**Option B: Unusual Field Formats**

- Invoice number that doesn't match pattern (e.g., "???" or very long random string)
- Vendor name that's all numbers or special characters
- These get lower confidence scores → review triggered if below threshold

### Method 3: Manual Testing (Quick)

You can also manually trigger by modifying the workflow temporarily:

1. **Force validation error**: Temporarily add a test validation error in `src/workflow/steps/validate.py`:

   ```python
   ctx.validation_errors = ["test_validation_error"]
   ctx.needs_review = True
   ```

2. **Force low confidence**: Temporarily lower confidence in `src/services/confidence.py`:
   ```python
   # In compute_field_confidence, return low scores:
   return 0.50  # Below 0.75 default threshold
   ```

## Testing Steps

1. **Start services**:

   ```bash
   # Terminal 1: API
   uvicorn src.app:app --reload

   # Terminal 2: Worker
   celery -A src.worker.celery_app worker -l INFO

   # Terminal 3: UI
   cd ui && npm run dev
   ```

2. **Upload a test document** via the UI (http://localhost:5173)

3. **Check worker logs** to see:
   - OCR text extraction
   - LLM extraction results
   - Confidence scores computed
   - Validation errors (if any)
   - Review item creation

4. **Check the queue**:
   - Open the UI dashboard
   - Click "Refresh" in the queue
   - You should see the review item if validation failed or confidence was low

5. **Check job status**:
   - The job status will show `review_pending` if a review item was created
   - Check `GET /v1/jobs/{job_id}` to see extraction + confidence scores

## Example: Creating a Test Document

If you don't have a problematic invoice, you can:

1. **Create a simple PDF** with minimal text:

   ```
   Invoice
   Total: $100
   ```

   - Missing: invoice_number, vendor_name, currency (if not "$"), invoice_date
   - This will trigger validation errors → review

2. **Use a non-invoice document**:
   - Upload a random PDF/image
   - LLM may extract fields poorly → low confidence → review

3. **Check existing outputs**:
   - Look in `outputs/json/` for examples
   - If any have `validation_errors` or low confidence, they should have review items

## Verifying Review Was Created

```bash
# Check queue endpoint
curl http://localhost:8000/v1/queue

# Check a specific job
curl http://localhost:8000/v1/jobs/{job_id}

# Check review stats
curl http://localhost:8000/v1/queue/stats
```

The extraction payload should include:

- `fields`: extracted values
- `confidence`: per-field confidence scores
- `validation_errors`: list of errors
- `status`: "review_pending" if review was triggered
