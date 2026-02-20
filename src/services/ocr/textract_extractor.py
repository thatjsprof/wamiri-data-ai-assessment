from __future__ import annotations

import io
import time
import uuid

import pdfplumber

from .textract_client import build_textract_deps
from .ocr_utils import textract_blocks_to_text


class TextractTextExtractor:
    def extract_text(self, file_bytes: bytes, content_type: str) -> str:
        deps = build_textract_deps()
        print(deps.bucket)

        if content_type in ("image/png", "image/jpeg", "image/jpg"):
            resp = deps.textract.detect_document_text(Document={"Bytes": file_bytes})
            return textract_blocks_to_text(resp.get("Blocks", []))

        if content_type in ("application/pdf", "application/octet-stream"):
            pages = self._count_pdf_pages(file_bytes)
            if pages <= 1:
                resp = deps.textract.detect_document_text(
                    Document={"Bytes": file_bytes}
                )
                return textract_blocks_to_text(resp.get("Blocks", []))

            key = f"textract-temp/{uuid.uuid4()}.pdf"
            deps.s3.put_object(
                Bucket=deps.bucket,
                Key=key,
                Body=file_bytes,
                ContentType="application/pdf",
            )
            try:
                start = deps.textract.start_document_text_detection(
                    DocumentLocation={"S3Object": {"Bucket": deps.bucket, "Name": key}}
                )
                job_id = start["JobId"]

                blocks: list[dict] = []
                next_token: str | None = None

                while True:
                    args = {"JobId": job_id}
                    if next_token:
                        args["NextToken"] = next_token

                    res = deps.textract.get_document_text_detection(**args)
                    status = res.get("JobStatus")

                    if status == "FAILED":
                        raise RuntimeError("textract_failed")

                    if status == "SUCCEEDED":
                        blocks.extend(res.get("Blocks", []))
                        next_token = res.get("NextToken")
                        if not next_token:
                            break
                    else:
                        time.sleep(1.0)

                return textract_blocks_to_text(blocks)
            finally:
                deps.s3.delete_object(Bucket=deps.bucket, Key=key)

        raise ValueError(f"unsupported_content_type:{content_type}")

    def _count_pdf_pages(self, pdf_bytes: bytes) -> int:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                return len(pdf.pages)
        except Exception:
            return 1
