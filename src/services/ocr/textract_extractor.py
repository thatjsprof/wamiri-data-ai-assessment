from __future__ import annotations

import io
import time
import uuid

import pdfplumber

from .textract_client import build_textract_deps
from .ocr_utils import textract_blocks_to_text
import logging

logger = logging.getLogger("docproc")


class TextractTextExtractor:
    def extract_text(self, file_bytes: bytes, content_type: str) -> str:
        try:
            deps = build_textract_deps()
        except RuntimeError as e:
            logger.warning("Textract deps unavailable (%s); returning empty text.", e)
            return ""

        if content_type in ("image/png", "image/jpeg", "image/jpg"):
            try:
                resp = deps.textract.detect_document_text(
                    Document={"Bytes": file_bytes}
                )
                return textract_blocks_to_text(resp.get("Blocks", []))
            except Exception as e:
                logger.warning(
                    "Textract sync image failed: %s; returning empty text.", e
                )
                return ""

        if content_type in ("application/pdf", "application/octet-stream"):
            pages = self._count_pdf_pages(file_bytes)
            if pages <= 1:
                try:
                    resp = deps.textract.detect_document_text(
                        Document={"Bytes": file_bytes}
                    )
                    return textract_blocks_to_text(resp.get("Blocks", []))
                except Exception as e:
                    logger.warning(
                        "Textract sync PDF failed: %s; returning empty text.", e
                    )
                    return ""

            key = f"textract-temp/{uuid.uuid4()}.pdf"
            try:
                deps.s3.put_object(
                    Bucket=deps.bucket,
                    Key=key,
                    Body=file_bytes,
                    ContentType="application/pdf",
                )
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
                        logger.warning(
                            "Textract job %s failed; returning empty text (job will go to review)",
                            job_id,
                        )
                        return ""

                    if status == "SUCCEEDED":
                        blocks.extend(res.get("Blocks", []))
                        next_token = res.get("NextToken")
                        if not next_token:
                            break
                    else:
                        time.sleep(1.0)

                return textract_blocks_to_text(blocks)
            except Exception as e:
                logger.warning(
                    "Textract S3/async failed (e.g. InvalidS3ObjectException): %s; returning empty text.",
                    e,
                )
                return ""
            finally:
                try:
                    deps.s3.delete_object(Bucket=deps.bucket, Key=key)
                except Exception:
                    pass

        logger.warning(
            "Unsupported content_type %s; returning empty text.", content_type
        )
        return ""

    def _count_pdf_pages(self, pdf_bytes: bytes) -> int:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                return len(pdf.pages)
        except Exception:
            return 1
