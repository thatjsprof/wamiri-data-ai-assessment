# Review queue design

## Goals
- Only send documents to humans when automation isn’t confident.
- Make sure the *right* items are reviewed first (priority + SLA).
- Ensure no two reviewers work on the same item.

## Data model
Stored in Postgres (`review_items`):

- `priority`: higher means earlier in the queue
- `sla_deadline`: deadline timestamp (used for ordering)
- `status`: pending / claimed / completed / rejected
- `assigned_to`: reviewer identifier
- `extraction_json`: snapshot shown to the reviewer
- `locked_fields`: human corrections to preserve

## Ordering
Queue ordering is:
1) priority DESC
2) sla_deadline ASC

Priority is computed based on how close the deadline is.

## Atomic claiming (no double assignment)
Claim uses:

`FOR UPDATE SKIP LOCKED`

So multiple reviewers can click “Claim next” at the same time and each will get a different item.

## Feedback loop (field locking)
When a reviewer corrects a field, we store it in `documents.locked_fields`.

On reprocessing:
- automated extraction runs
- then locked fields are merged on top

That means a human correction is never overwritten by automation.
