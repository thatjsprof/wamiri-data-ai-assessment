from __future__ import annotations

from dataclasses import dataclass
import boto3
from botocore.config import Config

from ...settings import settings


@dataclass(frozen=True)
class TextractDeps:
    textract: any
    s3: any
    bucket: str


def build_textract_deps() -> TextractDeps:
    if not settings.aws_textract_s3_bucket:
        raise RuntimeError(
            "AWS_TEXTRACT_S3_BUCKET is required for Textract async PDF OCR."
        )

    cfg = Config(retries={"max_attempts": 10, "mode": "standard"})
    textract = boto3.client("textract", region_name=settings.aws_region, config=cfg)
    s3 = boto3.client("s3", region_name=settings.aws_region, config=cfg)
    print(settings.aws_textract_s3_bucket, "uk,bkbhjvkuvkvukjgvjgvjgh")
    return TextractDeps(
        textract=textract, s3=s3, bucket=settings.aws_textract_s3_bucket
    )
