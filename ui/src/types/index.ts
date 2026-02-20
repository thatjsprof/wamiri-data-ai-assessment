export type ReviewItem = {
  id: string;
  document_id: string;
  job_id: string;
  created_at: string;
  sla_deadline: string;
  priority: number;
  status: string;
  assigned_to: string | null;
  reason: string;
  extraction?: {
    fields?: Record<string, unknown>;
    confidence?: Record<string, number>;
  } | Record<string, unknown>;
  locked_fields?: Record<string, unknown>;
};

export type ReviewMode = "view" | "correct";

export type ConfirmAction = "approve" | "reject" | null;

export type FieldSpec = {
  label: string;
  key: string;
  type?: string;
};
